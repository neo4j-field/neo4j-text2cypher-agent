"""
This code is based on content found in the LangGraph documentation: https://python.langchain.com/docs/tutorials/graph/#advanced-implementation-with-langgraph
"""

from langchain_core.prompts import ChatPromptTemplate


def create_text2cypher_validation_prompt_template() -> ChatPromptTemplate:
    """
    Create a Text2Cypher validation prompt template.

    Returns
    -------
    ChatPromptTemplate
        The prompt template.
    """

    validate_cypher_system = """
    You are a Cypher expert reviewing a statement written by a junior developer.
    """

    validate_cypher_user = """You must check the following:
    * Are there any syntax errors in the Cypher statement?
    * Are there any missing or undefined variables in the Cypher statement?
    * Does the Cypher statement include enough information to answer the question?
    * Ensure that all nodes, relationships and properties are present in the provided schema.

    CRITICAL INSTRUCTIONS FOR READING THE SCHEMA:
    - When you see a node label like "**Problem**" followed by properties like "`id`: STRING", this means the Problem label HAS the property 'id'
    - When you see a node label like "**Verbatim**" followed by properties like "`make`: STRING" and "`model`: STRING", this means the Verbatim label HAS both 'make' and 'model' properties
    - DO NOT claim a property doesn't exist if it's clearly listed under the node label in the schema
    - Read the schema carefully and thoroughly before making any error claims
    - If a property is listed in the schema under a node label, it EXISTS

    Examples of good errors:
    * Label (:Foo) does not exist, did you mean (:Bar)?
    * Property bar does not exist for label Foo, did you mean baz?
    * Relationship FOO does not exist, did you mean FOO_BAR?

    Schema:
    {schema}

    The question is:
    {question}

    The Cypher statement is:
    {cypher}

    DOUBLE-CHECK: Before reporting any property errors, verify that the property is NOT listed in the schema under the correct node label. Only report errors for properties that are truly missing from the schema."""

    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                validate_cypher_system,
            ),
            (
                "human",
                (validate_cypher_user),
            ),
        ]
    )
