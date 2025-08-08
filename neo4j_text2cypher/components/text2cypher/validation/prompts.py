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
    
    IMPORTANT: Be VERY careful when checking properties - many false errors are reported when properties actually exist!
    
    SPECIAL VALIDATION RULES:
    - String literals in WHERE clauses or functions are NOT label names - they are just string values
    - When you see patterns like tolower(x) = tolower("some_string"), the "some_string" is a string value, not a label
    - Only validate actual label references like (:LabelName) or n:LabelName against the schema
    - String values being compared or processed should NOT be validated as labels
    - Dynamic label checking (e.g., using labels(n) function) is for runtime matching, not compile-time validation

    CRITICAL INSTRUCTIONS FOR READING THE SCHEMA:
    - The schema follows a hierarchical structure:
      * Node labels appear as "- LabelName" (dash followed by the label name)
      * Properties appear indented under their node label as "  - propertyName: TYPE"
      * The indentation shows which properties belong to which node label
    - When validating labels: Look for exact matches in lines starting with "- " under "Node properties:"
    - When validating properties: Check the indented items under the corresponding node label
    - Labels and properties are CASE SENSITIVE - they must match EXACTLY as shown in the schema
    - DO NOT modify or "correct" label names - if a label uses underscores, mixed case, or specific spelling, use it exactly
    - DO NOT suggest similar-looking labels - only report if a label truly doesn't exist
    - Read the ENTIRE schema before claiming something is missing
    
    Schema Structure Example (generic):
    - NodeLabelA           <- This line defines a node label
      - property1: TYPE    <- These indented lines are properties of NodeLabelA
      - property2: TYPE    <- NodeLabelA.property2 EXISTS
    - NodeLabelB           <- This is a different node label
      - property3: TYPE    <- This property belongs to NodeLabelB
      
    To check if a property exists:
    1. Find the node label line (starts with "- ")
    2. Look at ALL indented properties below it
    3. If you see "  - propertyName:" under a node, that property EXISTS for that node
    4. NEVER report "Property 'x' does not exist" if you can find "  - x:" under the node label
    
    Relationships appear under "The relationships:" section in format:
    (:NodeA)-[:RELATIONSHIP_TYPE]->(:NodeB)

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
