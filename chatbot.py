import os
import getpass
import sqlite3
from pathlib import Path
import re
import gradio as gr
from openai import OpenAI

# Debug flag
SQL_DEBUG = os.getenv("SQL_DEBUG", "1").lower() in ("1", "true", "yes")

def _log(*args):
    if SQL_DEBUG:
        print("[SQLBot]", *args)

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=False)
    load_dotenv(override=False)
except Exception:
    pass

# Ensure API key
if not os.environ.get("OPENAI_API_KEY"):
    try:
        os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")
    except Exception:
        pass

client = OpenAI()
_log("API key loaded:", bool(os.environ.get("OPENAI_API_KEY")))

SCHEMA = """
Table: happiness
Columns:
    - "Overall rank" INTEGER
    - "Country or region" TEXT
    - "Score" REAL
    - "GDP per capita" REAL
    - "Social support" REAL
    - "Healthy life expectancy" REAL
    - "Freedom to make life choices" REAL
    - "Generosity" REAL
    - "Perceptions of corruption" REAL
    - "year" INTEGER
"""

SYSTEM_SQL = (
    "You convert natural language questions into a single ANSI SQL SELECT query "
    "for the provided World Happiness Report schema. "
    "Rules: Output only SQL, no markdown. "
    "Use only the given table/columns, and only SELECT statements. "
    "Always double-quote identifiers since they include spaces."
)

# Functions 
def generate_sql(question):
    messages = [
        {"role": "system", "content": SYSTEM_SQL},
        {"role": "user", "content": f"Schema:\n{SCHEMA}\n\nQuestion: {question}\nReturn only SQL."},
    ]
    resp = client.chat.completions.create(model="gpt-4o-mini", messages=messages, temperature=0)
    sql = resp.choices[0].message.content.strip().strip("`\n ")
    _log("Generated SQL:", sql)
    return sql

def _resolve_db_path():
    # Priority: env var, CWD happiness.db, preprocessing/happiness.db relative to this file
    env = os.getenv("HAPPINESS_DB_PATH")
    if env and os.path.exists(env):
        return env
    cwd_default = os.path.join(os.getcwd(), "happiness.db")
    if os.path.exists(cwd_default):
        return cwd_default
    alt = Path(__file__).resolve().parent / "preprocessing" / "happiness.db"
    if alt.exists():
        return str(alt)
    return None


def execute_sql(sql):
    db_path = _resolve_db_path()
    if not db_path:
        _log("No DB found. Set HAPPINESS_DB_PATH or place happiness.db in project or preprocessing/.")
        return None, None
    if not sql.lower().startswith("select"):
        return None, None

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        conn.close()
        _log(f"Executed on {db_path}, rows={len(rows)}")
        return cols, rows
    except Exception as e:
        _log("SQL error:", e)
        return None, None

def preview_table(cols, rows, max_rows=8):
    if not cols or not rows:
        return "(no results)"
    lines = [" | ".join(cols), " | ".join(["---"] * len(cols))]
    for r in rows[:max_rows]:
        lines.append(" | ".join(str(x) for x in r))
    if len(rows) > max_rows:
        lines.append(f"(+{len(rows)-max_rows} more rows...)")
    return "\n".join(lines)

def explain_result(question, sql, cols, rows):
    preview = preview_table(cols, rows)
    messages = [
        {"role": "system", "content": "You are a friendly data analyst explaining SQL query results clearly."},
        {"role": "user", "content": f"Question: {question}\n\nResult preview:\n{preview}"},
    ]
    resp = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    return resp.choices[0].message.content.strip()

def _latest_available_year(conn):
    try:
        cur = conn.cursor()
        cur.execute('SELECT MAX("year") FROM "happiness"')
        r = cur.fetchone()
        return r[0] if r and r[0] is not None else None
    except Exception as e:
        _log("Failed to get latest year:", e)
        return None


def _try_adjust_year(sql: str):
    # If SQL filters by a specific year that has no rows, try swapping to the latest available year
    m = re.search(r'WHERE\s+"year"\s*=\s*(\d{4})', sql, flags=re.IGNORECASE)
    if not m:
        return None, None
    requested_year = int(m.group(1))
    db_path = _resolve_db_path()
    if not db_path:
        return None, None
    try:
        conn = sqlite3.connect(db_path)
        # Check if requested year has any rows
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM "happiness" WHERE "year" = ?', (requested_year,))
        count = cur.fetchone()[0]
        if count and count > 0:
            conn.close()
            return None, None
        latest = _latest_available_year(conn)
        conn.close()
        if latest and latest != requested_year:
            adjusted_sql = re.sub(r'(WHERE\s+"year"\s*=\s*)(\d{4})', f"\\g<1>{latest}", sql, flags=re.IGNORECASE)
            return adjusted_sql, latest
    except Exception as e:
        _log("Year adjustment failed:", e)
    return None, None


def respond(message, history):
    sql = generate_sql(message)
    cols, rows = execute_sql(sql)

    adjusted_note = ""
    if cols is not None and (not rows or len(rows) == 0):
        adjusted_sql, latest = _try_adjust_year(sql)
        if adjusted_sql:
            _log(f"No rows for requested year; retrying with latest available year {latest}.")
            sql = adjusted_sql
            cols, rows = execute_sql(sql)
            if rows and len(rows) > 0:
                adjusted_note = f"\n\nNote: No rows for requested year; showing latest available year {latest}."

    explanation = explain_result(message, sql, cols, rows)
    preview = preview_table(cols, rows)
    final = (
        f"**Explanation:** {explanation}"
        f"{adjusted_note}\n\n"
        f"```sql\n{sql}\n```\n\n"
        f"{preview}"
    )
    history = history + [(message, final)]
    return history

# CSS
CSS = """
body {background-color:#0e0f13 !important;}
.gradio-container {max-width:850px !important;margin:auto;}
#chatbox .message.user {background:#2b2d31;color:white;border-radius:16px 16px 0 16px;padding:10px 14px;margin:6px 0;align-self:flex-end;max-width:80%;}
#chatbox .message.bot {background:#1d1f24;color:#e3e3e3;border-radius:16px 16px 16px 0;padding:10px 14px;margin:6px 0;align-self:flex-start;max-width:80%;}
#chatbox .message {display:flex;flex-direction:column;white-space:pre-wrap;font-family:Inter,system-ui,sans-serif;font-size:0.95rem;line-height:1.45;}
#input-area textarea {background:#1a1b1f;color:white;border:none;border-radius:10px;padding:12px;font-size:0.95rem;}
#input-area button {background:#10a37f;color:white;border:none;padding:10px 20px;border-radius:10px;font-weight:600;}
#header {text-align:center;padding:20px 0;color:white;font-family:Inter,sans-serif;}
"""

# Gradio UI
with gr.Blocks(css=CSS, analytics_enabled=False) as demo:
    gr.HTML("<h1 id='header'>World Happiness Chat</h1>")
    chatbot = gr.Chatbot(elem_id="chatbox", bubble_full_width=False, height=600)
    with gr.Row(elem_id="input-area"):
        msg = gr.Textbox(placeholder="Ask about happiness trends, rankings, averages...", lines=2, scale=4)
        send = gr.Button("Send", scale=1)
    examples = gr.Examples(
        examples=[
            "What were the top 5 happiest countries in 2019?",
            "Show the average \"Score\" per year between 2015 and 2019.",
            "Which country improved the most between 2015 and 2019?",
            "For Finland, show the happiness trend over the years.",
        ],
        inputs=msg,
    )
    send.click(respond, [msg, chatbot], [chatbot])
    msg.submit(respond, [msg, chatbot], [chatbot])

if __name__ == "__main__":
    demo.launch(inbrowser=True)
