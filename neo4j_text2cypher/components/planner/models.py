from typing import List

from pydantic import BaseModel, ConfigDict, Field

from neo4j_text2cypher.components.models import Task


class PlannerOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tasks: List[Task] = Field(
        default=[],
        description="A list of tasks that must be complete to satisfy the input question.",
    )
