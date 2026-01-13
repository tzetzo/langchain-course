import operator
from typing import TypedDict, List, Optional, Annotated
from pydantic import BaseModel


class PersonSummary(BaseModel):
    """The final structured JSON returned to the frontend."""

    summary: str
    facts: List[str]


class GraphState(TypedDict):
    person_name: str
    # By default, LangGraph overwrites keys. No need for operator.set.
    raw_data: str
    final_json: Optional[PersonSummary]
    # We use operator.add so that if multiple nodes return an error_count,
    # they are summed together rather than overwritten.
    error_count: Annotated[int, operator.add]
