import json
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from app.agent.agent import run_agent

EVALS_DIR = Path(__file__).resolve().parent
ROOT = EVALS_DIR.parents[1]
CASES_PATH = EVALS_DIR / "cases.json"
RESULTS_DIR = EVALS_DIR / "results"
CHECKS = ["tools", "hubs", "numbers", "empty", "forbidden", "grounded", "length", "plain"]
MAX_WORDS = 100
MARKDOWN_SYMBOLS = ["*", "#", "|"]


def block_value(block, key):
    # Assistant blocks are SDK objects, tool results are plain dicts.
    return block.get(key) if isinstance(block, dict) else getattr(block, key, None)


def tool_calls(messages):
    calls = []
    for message in messages:
        if message["role"] == "assistant":
            for block in message["content"]:
                if block_value(block, "type") == "tool_use" and block_value(block, "name") != "final_answer":
                    calls.append({"name": block_value(block, "name"), "input": block_value(block, "input")})
    return calls


def tool_results(messages):
    results = []
    for message in messages:
        if message["role"] == "user" and isinstance(message["content"], list):
            for block in message["content"]:
                if block_value(block, "type") == "tool_result" and not block_value(block, "is_error"):
                    results.append(block_value(block, "content"))
    return results


def numbers_in(value):
    # Every number inside a JSON value (nested dicts and lists included).
    if isinstance(value, bool):
        return []
    if isinstance(value, (int, float)):
        return [value]
    if isinstance(value, dict):
        value = list(value.values())
    if isinstance(value, list):
        found = []
        for item in value:
            found.extend(numbers_in(item))
        return found
    return []


def tool_numbers(messages):
    found = []
    for content in tool_results(messages):
        try:
            found.extend(numbers_in(json.loads(content)))
        except json.JSONDecodeError:
            pass  # e.g. "Answer accepted." for final_answer
    return found


def run_checks(case, final, messages):
    values = [number["value"] for number in final["key_numbers"]]
    called = [call["name"] for call in tool_calls(messages)]
    from_tools = tool_numbers(messages)

    checks = {
        "tools": all(name in called for name in case["expected_tools"]) if case["expected_tools"] else None,
        "hubs": all(hub in final["hubs"] for hub in case["expected_hubs"]) if case["expected_hubs"] else None,
        "numbers": all(value in values for value in case["expected_numbers"]) if case["expected_numbers"] else None,
        "empty": (not final["hubs"] and not final["key_numbers"]) if case["expect_empty"] else None,
        "forbidden": None,
        "grounded": all(value in from_tools for value in values),
        "length": len(final["answer"].split()) <= MAX_WORDS,
        "plain": not any(symbol in final["answer"] for symbol in MARKDOWN_SYMBOLS),
    }

    if "forbidden_numbers" in case:
        checks["forbidden"] = not any(
            number["hub_id"] == rule["hub_id"]
            and rule["label_contains"] in number["label"].lower()
            and number["value"] == rule["value"]
            for rule in case["forbidden_numbers"]
            for number in final["key_numbers"]
        )
    return checks


def run_case(case):
    messages = []
    for question in case["questions"]:
        messages.append({"role": "user", "content": question})
        final, messages = run_agent(messages)
    return final, messages


def format_check(result):
    if result is None:
        return "-"
    return "ok" if result else "FAIL"


def main():
    load_dotenv(ROOT / ".env")
    cases = json.loads(CASES_PATH.read_text())
    results = []
    passed_cases = 0
    passed_checks = 0
    total_checks = 0

    for case in cases:
        try:
            final, messages = run_case(case)
        except Exception as error:
            print(f"{case['id']:22} ERROR: {error}")
            results.append({"id": case["id"], "questions": case["questions"], "error": str(error)})
            continue

        checks = run_checks(case, final, messages)
        applied = [result for result in checks.values() if result is not None]
        passed_checks += sum(applied)
        total_checks += len(applied)
        if all(applied):
            passed_cases += 1

        print(f"{case['id']:22}" + "  ".join(f"{name} {format_check(checks[name]):4}" for name in CHECKS))
        results.append({
            "id": case["id"],
            "questions": case["questions"],
            "final_answer": final,
            "tool_calls": tool_calls(messages),
            "tool_results": tool_results(messages),
            "checks": checks,
        })

    print(f"\nCases passed: {passed_cases}/{len(cases)}   Checks passed: {passed_checks}/{total_checks}")

    RESULTS_DIR.mkdir(exist_ok=True)
    results_path = RESULTS_DIR / f"eval_{datetime.now():%Y-%m-%d_%H-%M-%S}.json"
    results_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Saved full results to {results_path}")


if __name__ == "__main__":
    main()
