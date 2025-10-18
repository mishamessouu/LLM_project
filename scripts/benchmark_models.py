"""
Benchmark OurSQLBot vs a baseline model on preset questions
-----------------------------------------------------------

For each question:
    - OurSQLBot: Generate SQL -> Execute -> Explain (natural-language answer grounded in DB)
    - Baseline: Ask the baseline chat model directly for a natural-language answer
    - Measure latency (ms) for each
    - Print and save results to benchmarks/answers.md

Run examples:
    python scripts\benchmark_models.py --baseline-model gpt-4o-mini
    python scripts\benchmark_models.py --baseline-model gpt-5
    python scripts\benchmark_models.py   # uses default baseline
"""

import time
import argparse
import os
from pathlib import Path
from openai import OpenAI
import importlib.util as import_util

# --- Load environment and API key ---
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=False)
    load_dotenv(override=False)
except Exception:
    pass

if not os.environ.get("OPENAI_API_KEY"):
    raise RuntimeError(" OPENAI_API_KEY not set. Please export it or add to .env")

client = OpenAI(timeout=25.0)

# --- Import local chatbot (same method as benchmark_models.py) ---
ROOT = Path(__file__).resolve().parents[1]
CHATBOT_PATH = ROOT / "chatbot.py"
spec = import_util.spec_from_file_location("chatbot", str(CHATBOT_PATH))
chatbot = import_util.module_from_spec(spec)
spec.loader.exec_module(chatbot)  # type: ignore

# --- Preset benchmark questions ---
QUESTIONS = [
    "According to the World Happiness Report, which country showed the greatest improvement in overall Happiness Score between 2015 and 2019?",
    "Based on the World Happiness Report, list the top 3 countries with the highest Social support for each year between 2015 and 2019.",
    "From the World Happiness Report, show Denmark’s Happiness Score for each year between 2015 and 2019, and include the change from the previous year.",
    "According to the World Happiness Report 2019, what was the average GDP per capita among the 10 happiest countries?",
    "Between 2015 and 2019, how did the average Healthy life expectancy score change overall according to the World Happiness Report?",
    "In the 2018 World Happiness Report data, which countries had a Freedom to make life choices score above the global average?",
    "According to the World Happiness Report 2019, what is the absolute difference in Happiness Score between the 1st and 10th ranked countries?",
    "Which country was ranked as the happiest in the world in the 2017 World Happiness Report?",
    "Which country had the highest GDP per capita in 2019 according to the World Happiness Report?",
    "According to the World Happiness Report, which country ranked lowest in Happiness Score in 2018?",
]


# --- Utility: safe call with fallback if temperature unsupported ---
def safe_completion(model: str, messages: list, temperature: float = 0):
    try:
        return client.chat.completions.create(model=model, messages=messages, temperature=temperature)
    except Exception as e:
        if "temperature" in str(e).lower():
            return client.chat.completions.create(model=model, messages=messages)
        raise

def timed_call(func, *args, **kwargs):
    t0 = time.perf_counter()
    try:
        result = func(*args, **kwargs)
    except Exception as e:
        result = f"[error: {e}]"
    t1 = time.perf_counter()
    return result, round((t1 - t0) * 1000, 1)

# --- Chatbot and baseline answer functions ---
def oursqlbot_answer(question: str) -> str:
    """Use our pipeline: NL -> SQL -> execute -> LLM explanation."""
    try:
        sql = chatbot.generate_sql(question)
        cols, rows = chatbot.execute_sql(sql)
        if cols is None:
            return f"[error: no database or failed execution]\nSQL: {sql}"
        explanation = chatbot.explain_result(question, sql, cols, rows)
        return explanation
    except Exception as e:
        return f"[error: {e}]"

def baseline_answer(question: str, model_id: str) -> str:
    resp = safe_completion(
        model=model_id,
        messages=[{"role": "user", "content": question}],
        temperature=0,
    )
    return resp.choices[0].message.content.strip()

# --- Main benchmark ---
def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--baseline-model", default="gpt-5", help="Baseline chat model id")
    return p.parse_args()


def main():
    args = parse_args()
    out_dir = ROOT / "benchmarks"
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "answers.md"

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Benchmark: OurSQLBot vs {args.baseline_model}\n\n")

        for idx, q in enumerate(QUESTIONS, 1):
            print(f"\n Question {idx}: {q}")

            ours_answer, ours_ms = timed_call(oursqlbot_answer, q)
            base_answer_text, base_ms = timed_call(baseline_answer, q, args.baseline_model)

            oa = ours_answer if isinstance(ours_answer, str) else str(ours_answer)
            ba = base_answer_text if isinstance(base_answer_text, str) else str(base_answer_text)

            print(f" OurSQLBot ({ours_ms} ms): {oa[:120]}{'...' if len(oa)>120 else ''}")
            print(f" {args.baseline_model} ({base_ms} ms): {ba[:120]}{'...' if len(ba)>120 else ''}")
            print("-" * 80)

            f.write(f"## Question {idx}: {q}\n\n")
            f.write(f"**OurSQLBot ({ours_ms} ms)**  \n{oa}\n\n")
            f.write(f"**{args.baseline_model} ({base_ms} ms)**  \n{ba}\n\n")
            f.write("---\n\n")

    print(f"\n✅ Results saved to: {md_path}")

if __name__ == "__main__":
    main()
