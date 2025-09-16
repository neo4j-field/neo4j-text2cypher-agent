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


def create_passthrough_prompt_template() -> ChatPromptTemplate:
    """
    Create a prompt for passthrough mode that resolves references but returns a single task.
    
    This is used when break_into_subquestions=False to ensure questions with
    ambiguous references are clarified using conversation history.
    
    Returns
    -------
    ChatPromptTemplate
        The prompt template for reference resolution in passthrough mode.
    """
    passthrough_system = """
You are a query processor in passthrough mode.
Your job is to take the user's question and pass it through UNCHANGED.

IMPORTANT RULES:
1. You must return exactly ONE task with the ORIGINAL question exactly as provided
2. DO NOT modify the question in any way
3. DO NOT resolve references like "those", "them", "it", "that", "their", "these", "which"
4. DO NOT add context from conversation history to the question
5. The task's question and parent_task should both be the original unmodified question

The generation node will handle reference resolution with full schema context.
Your only job is to pass the question through unchanged.

Example:
- Conversation history: "Q: Show me all customers from California  A: [list of California customers]"
- Current question: "What are their orders?"
- Output: Single task with question "What are their orders?" (UNCHANGED)
"""

    message = """{conversation_history}

Current question: {question}"""

    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                passthrough_system,
            ),
            (
                "human",
                message,
            ),
        ]
    )
