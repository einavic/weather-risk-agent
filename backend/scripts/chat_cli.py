import json
import logging
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from app.agent.agent import run_agent

ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = ROOT / "logs"


def setup_logging():
    LOGS_DIR.mkdir(exist_ok=True)
    log_path = LOGS_DIR / f"chat_{datetime.now():%Y-%m-%d_%H-%M-%S}.log"
    logging.basicConfig(
        filename=log_path,
        encoding="utf-8",
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # The SDK's HTTP library logs every request at INFO; keep only its warnings.
    logging.getLogger("httpx2").setLevel(logging.WARNING)
    return log_path


def print_tool_calls(new_messages):
    for message in new_messages:
        if message["role"] != "assistant":
            continue
        for block in message["content"]:
            if block.type == "tool_use" and block.name != "final_answer":
                print(f"  [tool] {block.name} {json.dumps(block.input)}")


def print_answer(final):
    print(f"\nAgent: {final['answer']}")
    for number in final["key_numbers"]:
        print(f"  {number['hub_id']:13} {number['label']}: {number['value']}")
    if final["caveat"]:
        print(f"Caveat: {final['caveat']}")


def main():
    load_dotenv(ROOT / ".env")
    log_path = setup_logging()
    print(f"Logging to {log_path}")
    print("Ask a question (empty line or 'quit' to exit).")

    messages = []
    while True:
        question = input("\nYou: ").strip()
        if question in ("", "quit", "exit"):
            break
        start = len(messages)
        messages.append({"role": "user", "content": question})
        final, messages = run_agent(messages)
        print_tool_calls(messages[start:])
        print_answer(final)


if __name__ == "__main__":
    main()
