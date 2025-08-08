"""
This code is based on content found in the LangGraph documentation: https://python.langchain.com/docs/tutorials/graph/#advanced-implementation-with-langgraph
"""

from langchain.prompts import ChatPromptTemplate


def create_text2cypher_correction_prompt_template() -> ChatPromptTemplate:
    """
    Create a Text2Cypher query correction prompt template.

    Returns
    -------
    ChatPromptTemplate
        The prompt template.
    """
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "You are a Cypher expert reviewing a statement written by a junior developer. "
                    "You need to correct the Cypher statement based on the provided errors. No pre-amble."
                    "Do not wrap the response in any backticks or anything else. Respond with a Cypher statement only!"
                ),
            ),
            (
                "human",
                (
                    """Check for invalid syntax or semantics and return a corrected Cypher statement.

    IMPORTANT: Be VERY careful when checking the schema - the errors you received might be incorrect!
    
    SPECIAL VALIDATION RULES (ignore errors about these):
    - String literals in WHERE clauses or functions are NOT label names - they are just string values
    - When you see patterns like tolower(x) = tolower("some_string"), the "some_string" is a string value, not a label
    - Only actual label references like (:LabelName) or n:LabelName need to match the schema
    - String values being compared or processed should NOT be changed to match schema labels
    - Dynamic label checking (e.g., using labels(n) function) is for runtime matching - keep the original strings
    
    CRITICAL INSTRUCTIONS FOR READING THE SCHEMA:
    - The schema follows a hierarchical structure:
      * Node labels appear as "- LabelName" (dash followed by the label name)
      * Properties appear indented under their node label as "  - propertyName: TYPE"
    - Labels and properties are CASE SENSITIVE - use them EXACTLY as shown in the schema
    - DO NOT modify or "correct" label names - if the error says a label doesn't exist, check the schema for the exact spelling
    - When correcting based on errors, ensure you're using the exact label/property names from the schema
    
    To verify if a property exists before "correcting" it:
    1. Find the node label line (starts with "- ")
    2. Look at ALL indented properties below it
    3. If you see "  - propertyName:" under a node, that property EXISTS for that node
    4. If the error says "Property 'x' does not exist" but you find "  - x:" under the node, IGNORE that error - the property DOES exist

    Schema:
    {schema}

    Note: Do not include any explanations or apologies in your responses.
    Do not wrap the response in any backticks or anything else.
    Respond with a Cypher statement only!

    Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.

    The question is:
    {question}

    The Cypher statement is:
    {cypher}

    The errors are:
    {errors}

    Corrected Cypher statement: """
                ),
            ),
        ]
    )
