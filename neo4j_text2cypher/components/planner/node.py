from typing import Any, Callable, Coroutine, Dict, List

from langchain_core.language_models import BaseChatModel
from langchain_core.runnables.base import Runnable

from neo4j_text2cypher.components.models import Task
from neo4j_text2cypher.components.planner.models import PlannerOutput
from neo4j_text2cypher.components.planner.prompts import create_planner_prompt_template
from neo4j_text2cypher.components.state import InputState

def format_conversation_history(history: List[Dict[str, Any]]) -> str:
    """
    Format conversation history for the planner prompt.

    Parameters
    ----------
    history : List[Dict[str, Any]]
        The conversation history.

    Returns
    -------
    str
        Formatted conversation history string.
    """
    if not history:
        return "No previous conversation history."

    formatted_history = "Previous conversation history:\n"
    for i, record in enumerate(history, 1):
        formatted_history += f"\n{i}. Q: {record['question']}\n"
        formatted_history += f"   A: {record['answer']}\n"

    return formatted_history


def create_planner_node(
    llm: BaseChatModel, break_into_subquestions: bool = True
) -> Callable[[InputState], Coroutine[Any, Any, Dict[str, Any]]]:
    """
    Create a planner node to be used in a LangGraph workflow.

    Parameters
    ----------
    llm : BaseChatModel
        The LLM used to process data.
    break_into_subquestions : bool, optional
        Whether to break complex questions into sub-questions or pass through directly, by default True

    Returns
    -------
    Callable[[InputState], OverallState]
        The LangGraph node.
    """

    planner_prompt = create_planner_prompt_template()
    planner_chain: Runnable[Dict[str, Any], Any] = (
        planner_prompt
        | llm.with_structured_output(PlannerOutput, method="function_calling")
    )

    async def planner(state: InputState) -> Dict[str, Any]:
        """
        Break user query into chunks, if appropriate.
        """

        if break_into_subquestions:
            # Use AI to break down the question into multiple tasks
            history = state.get("history", [])
            conversation_history = format_conversation_history(history)

            planner_output: PlannerOutput = await planner_chain.ainvoke(
                {
                    "question": state.get("question", ""),
                    "conversation_history": conversation_history,
                }
            )

        else:
            # Passthrough mode: directly create a single task with the original question
            # No AI needed - deterministic and reliable
            original_question = state.get("question", "")
            planner_output = PlannerOutput(tasks=[
                Task(
                    question=original_question,
                    parent_task=original_question,
                )
            ])
        final_tasks = planner_output.tasks or [
            Task(
                question=state.get("question", ""),
                parent_task=state.get("question", ""),
            )
        ]
        
        task_count = len(final_tasks)
        if task_count > 1:
            print(f"\n🎯 Planner: Breaking into {task_count} sub-tasks")
        else:
            print(f"\n🎯 Planner: Processing as single task")
        
        return {
            "tasks": final_tasks,
            "steps": ["planner"],
        }

    return planner
