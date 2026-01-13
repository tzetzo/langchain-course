# src/schema.py
from pydantic import BaseModel, Field
from typing import List


class PersonSummary(BaseModel):
    summary: str = Field(description="A 2-3 sentence professional summary.")
    facts: List[str] = Field(description="3 interesting or key facts about the person.")
