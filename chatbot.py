import os
import json
import getpass
import sqlite3
import gradio as gr
from openai import OpenAI


# OpenAI client
client = OpenAI()


# Ensure OPENAI_API_KEY is set
if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")


# World Happiness Report SQL schema (example)
SCHEMA = """
Table: happiness
Columns:
  - country TEXT
  - year INTEGER
  - happiness_score REAL           -- overall life evaluation (0-10)
  - gdp_per_capita REAL
  - social_support REAL
  - healthy_life_expectancy REAL
  - freedom_to_make_life_choices REAL
  - generosity REAL
  - perceptions_of_corruption REAL
  - rank INTEGER                   -- rank in that year (1 = highest)
  - continent TEXT                 -- optional; if present in your DB
"""


SYSTEM_SQL = (
    "You convert natural language questions into a single ANSI SQL SELECT query "
    "for the provided World Happiness Report schema. "
    "Follow rules: (1) Output only SQL; no code fences or commentary. "
    "(2) Use only tables/columns from the schema. (3) Prefer safe SELECT queries; "
    "never write INSERT/UPDATE/DELETE/DROP. (4) If the request is ambiguous, choose a "
    "reasonable interpretation and include clear filters/aggregations."
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
    return sql


def execute_sql(sql: str, max_rows: int = 200):
    """Execute a read-only SQL query against a SQLite DB if configured.
    The DB file path should be provided via env var HAPPINESS_DB_PATH.
    Returns (columns: list[str], rows: list[list|tuple]) or (None, None) if unavailable.
    """
    db_path = os.getenv("HAPPINESS_DB_PATH")
    if not db_path:
        return None, None
    if not os.path.exists(db_path):
        return None, None
    # Only allow SELECT for safety
    if not sql.strip().lower().startswith("select"):
        return None, None
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchmany(max_rows)
        columns = [desc[0] for desc in cur.description] if cur.description else []
        conn.close()
        return columns, rows
    except Exception:
        # On any DB error, don't crash chat; just return None so we can still show SQL
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
                "You are a data analyst. Provide a concise, clear explanation of the SQL result "
                "for a non-technical user. If there is data, summarize key takeaways and any apparent trends; "
                "if there is no data available, describe what the query intends to fetch."
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
    return resp.choices[0].message.content.strip()

def respond(message, image, history):
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
        f"SQL:\n```sql\n{sql}\n```\n\n"
        f"Preview:\n{preview_block}"
    )

    history = history + [(message if message else "[Image]", display)]
    yield history


# Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("## World Happiness SQL Genie")
    chatbot = gr.Chatbot()
    with gr.Row():
        msg = gr.Textbox(placeholder="Ask a question about World Happiness (e.g., rankings, averages, trends)...", lines=2)
        img = gr.Image(type="filepath", label="Optional image")

    # Example prompts
    gr.Examples(
        examples=[
            "What were the top 5 happiest countries in 2021?",
            "Show the average happiness_score by continent in 2019, sorted descending.",
            "Which country improved its rank the most between 2015 and 2020?",
            "List the top 10 countries by happiness_score and their gdp_per_capita in 2022.",
            "For Finland, show happiness_score over time.",
        ],
        inputs=msg,
    )

    submit = gr.Button("Send")
    clear = gr.Button("Clear Chat")

    # analyze image silently (not used for SQL)
    img.upload(lambda p: None, [img], None)

    submit.click(respond, [msg, img, chatbot], [chatbot])
    msg.submit(respond, [msg, img, chatbot], [chatbot])
    clear.click(lambda: [], None, chatbot)


if __name__ == "__main__":
    demo.launch(inbrowser=True)