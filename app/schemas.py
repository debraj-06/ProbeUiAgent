from typing import Literal
from pydantic import BaseModel, Field

Severity = Literal["critical", "high", "medium", "low"]
Category = Literal["UI", "UX", "Frontend"]
Viewport = Literal["desktop", "tablet", "mobile", "all"]


class Bug(BaseModel):
    category: Category
    title: str
    severity: Severity
    confidence: float = Field(ge=0, le=1)
    description: str
    evidence: str
    viewport: Viewport
    selector: str = ""
    recommended_fix: str


class BugAnalysis(BaseModel):
    summary: str
    bugs: list[Bug]
