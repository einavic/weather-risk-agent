import json
import logging

import anthropic
from pydantic import ValidationError

from app.agent.schema import FinalAnswer
from app.agent.tools import TOOL_FUNCTIONS, TOOLS

MODEL = "claude-opus-5-5"
MAX_TOKENS = 16000
MAX_TURNS = 8

SYSTEM_PROMPT = """
You are a weather risk analyst for a logistics company.
Severe weather shuts hubs down, delays shipments and costs the company money. Each year the company chooses a handful of hubs to invest in resilience upgrades.
You help analysts decide which distribution hubs to prioritise for resilience investment - which hubs are most exposed to weather disruption.

Data: 12 fixed US hubs. Daily weather for 2021-01-01 to 2025-12-31, and FEMA
major disaster declarations for 2006-2025. "Last year" means 2025. If asked
about a hub or a period outside this data, say it is not covered and name
what is.

Rules:
- Every number in your answer must come from a tool result. Never estimate, guess,
  calculate or sort numbers yourself.
- Scores are 0-100 and measure how often a hazard occurred in the past. They
  are not forecasts and do not measure how severe each event was.
- The composite is a weighted sum of four hazard scores. When you explain a
  composite, quote the weights from the tool result and say they are a
  judgment of how long each hazard typically closes a hub, not measured cost.
- When you give a score, name the hazard that drives it and give the main raw
  metric behind it (for example days per year). Do not give a bare number.
- When you recommend a hub for investment, name the hub and the hazard to
  address, and nothing more. Do not suggest specific measures, equipment or
  projects; the data does not support them.
- Hurricane-related flooding is counted under hurricane, not flood. Mention
  this when discussing flood scores for coastal hubs such as Miami.
- Wind is not scored, because the wind data does not capture hurricane
  gusts reliably.
- If a question is ambiguous, ask one short clarifying question.

Answer style:
- Write plain text for a person to read. No Markdown: no asterisks, headings,
  tables or bullet lists.
- Be brief: lead with the direct answer, usually in 2 to 5 sentences. Add
  more only if the question asks for it.
- Put the single caveat that matters most in the caveat field, not in answer.

Finishing:
- Always finish by calling the final_answer tool, never with plain text.
  Call it on its own, after any other tools.
- answer follows the answer style rules above.
- hubs lists the hub ids the answer is about.
- key_numbers holds the main numbers from your answer. Every value must be
  copied exactly from a tool result. Use a short label, such as
  "winter score" or "snow days per year".
- If you need to ask a clarifying question, put it in answer and leave
  hubs and key_numbers empty.
"""

logger = logging.getLogger(__name__)


def run_tool(name, tool_input):
    logger.info("Tool call: %s %s", name, json.dumps(tool_input))
    try:
        result = TOOL_FUNCTIONS[name](**tool_input)
    except Exception as error:
        logger.error("Tool %s failed: %s", name, error)
        return {"type": "tool_result", "content": f"Error: {error}", "is_error": True}
    content = json.dumps(result)
    logger.info("Tool result: %s %s", name, content)
    return {"type": "tool_result", "content": content}


def run_agent(messages):
    logger.info("Question: %s", messages[-1]["content"])
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment

    failures = 0

    for _ in range(MAX_TURNS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        # Every tool_use block needs a tool_result, including final_answer,
        # otherwise the API rejects the next follow-up question.
        reply = []
        final = None
        error = None
        for block in response.content:
            if block.type != "tool_use":
                continue
            if block.name == "final_answer":
                try:
                    final = FinalAnswer.model_validate(block.input)
                    reply.append({"type": "tool_result", "tool_use_id": block.id, "content": "Answer accepted."})
                except ValidationError as validation_error:
                    error = f"final_answer was not valid: {validation_error}"
                    reply.append({"type": "tool_result", "tool_use_id": block.id, "content": error, "is_error": True})
            else:
                result = run_tool(block.name, block.input)
                result["tool_use_id"] = block.id
                reply.append(result)

        if response.stop_reason != "tool_use":
            error = f"You replied with plain text (stop_reason={response.stop_reason}). Always finish by calling the final_answer tool."
            reply.append({"type": "text", "text": error})

        if reply:
            messages.append({"role": "user", "content": reply})

        if final is not None:
            logger.info("Final answer: %s", final.model_dump_json())
            return final.model_dump(), messages

        if error is not None:
            failures += 1
            logger.warning("Invalid final answer (%d of 2): %s", failures, error)
            if failures == 2:
                raise RuntimeError("Model did not return a valid final answer")

    logger.warning("Reached MAX_TURNS=%d without a final answer", MAX_TURNS)
    answer = {
        "answer": "Sorry, I could not complete this question. Please try asking it in a simpler way.",
        "hubs": [],
        "key_numbers": [],
        "caveat": "",
    }
    return answer, messages
