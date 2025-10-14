import os
import json
import getpass
import sqlite3
from pathlib import Path
import gradio as gr
from openai import OpenAI
# Debug logging flag (set SQL_DEBUG=0 to disable)
SQL_DEBUG = os.getenv("SQL_DEBUG", "1").lower() in ("1", "true", "yes")


def _log(*args):
    if SQL_DEBUG:
        print("[SQLBot]", *args)


# Load environment variables from .env if present (optional)
try:
    from dotenv import load_dotenv  # type: ignore
    # search from current file upward
    load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=False)
    load_dotenv(override=False)  # also load from CWD if any
except Exception:
    pass

# Ensure OPENAI_API_KEY is set (prompt as last resort in interactive shell)
if not os.environ.get("OPENAI_API_KEY"):
    try:
        os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")
    except Exception:
        # non-interactive context, leave unset so we can error later with a clear message
        pass

# OpenAI client (after env is loaded)
client = OpenAI()
_log("OPENAI_API_KEY loaded:", bool(os.environ.get("OPENAI_API_KEY")))


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
    "Follow rules: (1) Output only SQL; no code fences or commentary. "
    "(2) Use only tables/columns from the schema. (3) Prefer safe SELECT queries; "
    "never write INSERT/UPDATE/DELETE/DROP. (4) If the request is ambiguous, choose a "
    "reasonable interpretation and include clear filters/aggregations. "
    "(5) Because column names include spaces, always double-quote identifiers, e.g., \"Score\", \"Overall rank\", \"year\"."
)


def generate_sql(user_question: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_SQL},
        {
            "role": "user",
            "content": (
                "Schema:\n" + SCHEMA + "\n\nQuestion: " + user_question + "\n\nReturn only SQL."
            ),
        },
    ]

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0,
    )
    sql = resp.choices[0].message.content.strip()
    # Ensure no backticks
    if sql.startswith("```"):
        sql = sql.strip("`\n ")
    _log("Generated SQL for question:", user_question)
    _log(sql)
    return sql


def execute_sql(sql: str, max_rows: int = 200):
    """Execute a read-only SQL query against a SQLite DB if configured.
    The DB file path should be provided via env var HAPPINESS_DB_PATH.
    Returns (columns: list[str], rows: list[list|tuple]) or (None, None) if unavailable.
    """
    # Resolve DB path with fallbacks
    db_path = os.getenv("HAPPINESS_DB_PATH")
    if not db_path:
        # common local paths based on your preprocessing scripts
        candidates = [
            os.path.join("preprocessing", "happiness.db"),
            os.path.join(".", "happiness.db"),
        ]
        for c in candidates:
            if os.path.exists(c):
                db_path = c
                break
    if not db_path:
        _log("No DB path found; set HAPPINESS_DB_PATH if you want execution previews.")
        return None, None
    if not os.path.exists(db_path):
        _log("DB path does not exist:", db_path)
        return None, None
    # Only allow SELECT for safety
    if not sql.strip().lower().startswith("select"):
        _log("Blocked non-SELECT statement:", sql.split("\n")[0][:120])
        return None, None
    try:
        _log("Executing on DB:", db_path)
        _log("SQL head:", sql.split("\n")[0][:200])
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchmany(max_rows)
        columns = [desc[0] for desc in cur.description] if cur.description else []
        conn.close()
        _log(f"Rows fetched: {len(rows)}; Columns: {columns}")
        return columns, rows
    except Exception as e:
        # On any DB error, don't crash chat; just return None so we can still show SQL
        _log("DB error during execution:", e)
        return None, None


def _preview_table(columns, rows, max_rows: int = 10) -> str:
    if not columns or not rows:
        return "(no rows)"
    head = rows[:max_rows]
    # Build a simple pipe-separated preview
    lines = []
    lines.append(" | ".join(map(str, columns)))
    lines.append(" | ".join(["---"] * len(columns)))
    for r in head:
        # r may be tuple
        lines.append(" | ".join(map(lambda x: str(x) if x is not None else "", r)))
    more = "" if len(rows) <= max_rows else f"\n(+{len(rows)-max_rows} more rows truncated)"
    return "\n".join(lines) + more


def generate_explanation(question: str, sql: str, columns, rows) -> str:
    """Use OpenAI to provide a concise explanation of the result.
    If rows are present, summarize insights; otherwise, explain what the SQL would retrieve.
    """
    table_preview = _preview_table(columns, rows) if columns is not None else "(no data)"
    messages = [
        {
            "role": "system",
            "content": (
                "You are a data analyst. Provide a concise, clear explanation of the SQL result"
                "for a non-technical user. If there is data, summarize key takeaways and any apparent trends; "
                "if there is no data available, describe what the query intends to fetch."
                "do not mention the SQL itself."
            ),
        },
        {
            "role": "user",
            "content": (
                "Question: "
                + question
                + "\n\nSQL:\n"
                + sql
                + "\n\nColumns: "
                + (", ".join(columns) if columns else "")
                + "\nSample rows (truncated):\n"
                + table_preview
            ),
        },
    ]
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0,
    )
    explanation = resp.choices[0].message.content.strip()
    _log("Generated explanation (first 200 chars):", explanation[:200])
    return explanation

def respond(message, history):
    if message is None:
        message = ""

    # 1) Generate SQL from question
    try:
        sql = generate_sql(message)
    except Exception as e:
        sql = f"-- Error generating SQL: {e}"

    # 2) Try to execute and fetch sample rows
    columns, rows = execute_sql(sql)

    # 3) Generate natural-language explanation of the (intended) result
    try:
        explanation = generate_explanation(message, sql, columns, rows)
    except Exception as e:
        explanation = f"Failed to interpret result: {e}"

    # 4) Build display payload: explanation first, then SQL, then small preview
    preview_block = _preview_table(columns, rows) if columns is not None else "(DB not configured; set HAPPINESS_DB_PATH)"
    display = (
        f"Explanation:\n{explanation}\n\n"
        #f"SQL:\n```sql\n{sql}\n```\n\n"
        #f"Preview:\n{preview_block}"
    )

    # Print the final payload to console for visibility
    _log("Final response payload:\n" + display)

    history = history + [(message, display)]
    yield history


# Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("## World Happiness SQL Genie")
    chatbot = gr.Chatbot()
    with gr.Row():
        msg = gr.Textbox(placeholder="Ask a question about World Happiness (e.g., rankings, averages, trends)...", lines=2)

    # Example prompts
    gr.Examples(
        examples=[
            "What were the top 5 happiest countries in 2019?",
            "Show the average \"Score\" by year between 2015 and 2029, sorted descending.",
            "Which country improved its rank the most between 2015 and 2019?",
            "List the top 10 countries by \"Score\" and their \"GDP per capita\" in 2018.",
            "For Finland, show \"Score\" over time.",
        ],
        inputs=msg,
    )

    submit = gr.Button("Send")
    clear = gr.Button("Clear Chat")

    submit.click(respond, [msg, chatbot], [chatbot])
    msg.submit(respond, [msg, chatbot], [chatbot])
    clear.click(lambda: [], None, chatbot)


if __name__ == "__main__":
    demo.launch(inbrowser=True)