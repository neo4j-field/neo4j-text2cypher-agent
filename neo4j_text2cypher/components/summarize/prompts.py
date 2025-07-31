from langchain.prompts import ChatPromptTemplate


def create_summarization_prompt_template() -> ChatPromptTemplate:
    """
    Create a summarization prompt template.

    Returns
    -------
    ChatPromptTemplate
        The prompt template.
    """

    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful assistant",
            ),
            (
                "human",
                (
                    """Fact: {results}

{conversation_history}

    * Summarise the above fact as if you are answering this question "{question}"
    * When the fact is not empty, assume the question is valid and the answer is true
    * Do not return helpful or extra text or apologies
    * Just return summary to the user. DO NOT start with "Here is a summary"
    * List the results in rich text format if there are more than one results
    * Don't report empty String results, but include results that are 0 or 0.0.
    * IMPORTANT: If conversation history is provided and the current question refers to previous context (like "those", "them", "it"), use the history to provide proper context in your response."""
                ),
            ),
        ]
    )
