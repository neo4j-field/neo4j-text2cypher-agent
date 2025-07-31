class Neo4jText2CypherError(Exception):
    """Global Exception for Neo4j Text2Cypher package."""

    ...


class CypherExampleRetrieverError(Neo4jText2CypherError):
    """Exception raised when an error occurs while a Cypher Example Retriever is retrieving examples."""

    ...


class CypherQueryNodesReadError(Neo4jText2CypherError):
    """Exception raised when an error occurs while retrieving all existing Cypher query node ids."""

    ...
