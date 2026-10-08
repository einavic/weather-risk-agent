from typing import Literal

from pydantic import BaseModel, Field

from app.agent.tools import HUB_IDS

# Only the 12 hub ids from data/hubs.json are allowed.
HubId = Literal[tuple(HUB_IDS)]


class KeyNumber(BaseModel):
    hub_id: HubId
    label: str
    # strict: reject text such as "12.5" instead of converting it to a number.
    value: float = Field(strict=True)


class FinalAnswer(BaseModel):
    answer: str
    hubs: list[HubId]
    key_numbers: list[KeyNumber]
    caveat: str
