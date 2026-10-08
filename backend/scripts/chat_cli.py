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
            if block.type == "tool_use":
                print(f"  [tool] {block.name} {json.dumps(block.input)}")


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
        answer, messages = run_agent(messages)
        print_tool_calls(messages[start:])
        print(f"\nAgent: {answer}")


if __name__ == "__main__":
    main()
