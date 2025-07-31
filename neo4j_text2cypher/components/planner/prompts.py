from langchain_core.prompts import ChatPromptTemplate

planner_system = """
You must analyze the input question and break it into individual sub tasks.
If appropriate independent tasks exist, then provide them as a list, otherwise return an empty list.
Tasks should NOT be dependent on each other.
Return a list of tasks to be completed.

IMPORTANT: When analyzing the current question, consider the conversation history provided. 
If the current question contains references like "those", "them", "it", "that", or similar pronouns, 
these may refer to entities or concepts from previous questions in the conversation. 
Use this context to understand what the user is asking about.
"""

def create_planner_prompt_template() -> ChatPromptTemplate:
    """
    Create a planner prompt template for breakdown mode.
    
    Note: This is only used when break_into_subquestions=True.
    Passthrough mode doesn't use AI at all.

    Returns
    -------
    ChatPromptTemplate
        The prompt template for question breakdown.
    """
    message = """Rules:
* When a user asks the same or similar question again, provide a fresh, complete answer with full task breakdown - users want complete responses even for repeated questions.
* Ensure that tasks within the current question are not returning duplicated or similar information to each other.
* Ensure that tasks are NOT dependent on information gathered from other tasks!
* tasks that are dependent on each other should be combined into a single question.
* tasks that return the same information should be combined into a single question.

{conversation_history}

question: {question}
"""
    
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                planner_system,
            ),
            (
                "human",
                message,
            ),
        ]
    )
