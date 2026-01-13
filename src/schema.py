# src/schema.py
from pydantic import BaseModel, Field
from typing import List


class PersonSummary(BaseModel):
    summary: str = Field(description="A professional summary of the person.")
    facts: List[str] = Field(description="3 key professional facts.")
    linkedin_url: str = Field(
        description="The direct URL to the person's LinkedIn profile."
    )
