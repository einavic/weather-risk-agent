import json
import logging

import anthropic

from app.tools import TOOL_FUNCTIONS, TOOLS

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
- Give at most one caveat, the one that matters most for this question.
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

    for _ in range(MAX_TURNS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            if response.stop_reason != "end_turn":
                logger.warning("Stopped with stop_reason=%s", response.stop_reason)
            answer = "".join(block.text for block in response.content if block.type == "text")
            logger.info("Answer:\n%s", answer)
            return answer, messages

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = run_tool(block.name, block.input)
                result["tool_use_id"] = block.id
                tool_results.append(result)
        messages.append({"role": "user", "content": tool_results})

    logger.warning("Reached MAX_TURNS=%d without a final answer", MAX_TURNS)
    answer = "Sorry, I could not complete this question. Please try asking it in a simpler way."
    return answer, messages
