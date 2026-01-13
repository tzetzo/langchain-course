import operator
from typing import TypedDict, List, Optional, Annotated
from src.schema import PersonSummary

class GraphState(TypedDict):
    person_name: str
    # By default, LangGraph overwrites keys. No need for operator.set.
    raw_data: str
    final_json: Optional[PersonSummary]
    # We use operator.add so that if multiple nodes return an error_count,
    # they are summed together rather than overwritten.
    error_count: Annotated[int, operator.add]
    # NEW: Track verification status
    is_verified: bool
    retry_count: Annotated[int, operator.add]
    