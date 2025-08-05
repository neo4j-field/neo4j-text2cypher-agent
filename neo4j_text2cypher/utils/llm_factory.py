"""LLM factory for creating configured language model instances."""

import os
from typing import TYPE_CHECKING

from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings

if TYPE_CHECKING:
    from neo4j_text2cypher.utils.config import ConfigLoader


def create_llm(config_loader: "ConfigLoader") -> BaseChatModel:
    """
    Create a language model instance from configuration.
    
    Supports OpenAI and Azure OpenAI providers based on configuration settings.
    API keys are loaded from environment variables for security.
    
    Parameters
    ----------
    config_loader : ConfigLoader
        Configuration loader instance containing LLM settings
        
    Returns
    -------
    BaseChatModel
        Configured language model instance ready for use
        
    Raises
    ------
    ValueError
        If unsupported provider is specified or required configuration is missing
    ImportError
        If required LLM provider package is not installed
    RuntimeError
        If required environment variables (API keys) are not set
        
    Examples
    --------
    >>> from neo4j_text2cypher.utils.config import ConfigLoader
    >>> from neo4j_text2cypher.utils.llm_factory import create_llm
    >>> 
    >>> config_loader = ConfigLoader("app-config.yml")
    >>> llm = create_llm(config_loader)
    >>> response = await llm.ainvoke("Hello world")
    """
    llm_config = config_loader.get_llm_config()
    
    if llm_config.provider == "openai":
        return _create_openai_llm(llm_config)
    elif llm_config.provider == "azure_openai":
        return _create_azure_openai_llm(llm_config)
    else:
        raise ValueError(
            f"Unsupported LLM provider: {llm_config.provider}. "
            f"Supported providers: 'openai', 'azure_openai'"
        )


def _create_openai_llm(llm_config) -> BaseChatModel:
    """
    Create OpenAI ChatOpenAI instance.
    
    Parameters
    ----------
    llm_config : LLMConfig
        LLM configuration containing model and temperature settings
        
    Returns
    -------
    ChatOpenAI
        Configured OpenAI language model instance
        
    Raises
    ------
    ImportError
        If langchain-openai package is not installed
    RuntimeError
        If OPENAI_API_KEY environment variable is not set
    """
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as e:
        raise ImportError(
            "langchain-openai package is required for OpenAI provider. "
            "Install it with: pip install langchain-openai"
        ) from e
    
    # Verify API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY environment variable is required for OpenAI provider"
        )
    
    return ChatOpenAI(
        model=llm_config.model,
        temperature=llm_config.temperature,
        api_key=api_key,
    )


def _create_azure_openai_llm(llm_config) -> BaseChatModel:
    """
    Create Azure OpenAI AzureChatOpenAI instance.
    
    Parameters
    ----------
    llm_config : LLMConfig
        LLM configuration containing model, temperature, and Azure-specific settings
        
    Returns
    -------
    AzureChatOpenAI
        Configured Azure OpenAI language model instance
        
    Raises
    ------
    ImportError
        If langchain-openai package is not installed
    RuntimeError
        If required Azure OpenAI environment variables are not set
    """
    try:
        from langchain_openai import AzureChatOpenAI
    except ImportError as e:
        raise ImportError(
            "langchain-openai package is required for Azure OpenAI provider. "
            "Install it with: pip install langchain-openai"
        ) from e
    
    # Verify required Azure environment variables
    required_env_vars = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT", 
        "AZURE_OPENAI_API_VERSION"
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        raise RuntimeError(
            f"Missing required environment variables for Azure OpenAI: {missing_vars}"
        )
    
    return AzureChatOpenAI(
        azure_deployment=llm_config.model,
        temperature=llm_config.temperature,
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )


def create_embeddings(config_loader: "ConfigLoader") -> Embeddings:
    """
    Create an embeddings model instance that matches the LLM provider configuration.
    
    Uses the same API credentials and provider as the configured LLM to ensure
    compatibility and avoid additional setup requirements.
    
    Parameters
    ----------
    config_loader : ConfigLoader
        Configuration loader instance containing LLM settings
        
    Returns
    -------
    Embeddings
        Configured embeddings model instance ready for use
        
    Raises
    ------
    ValueError
        If unsupported provider is specified
    ImportError
        If required embeddings provider package is not installed
    RuntimeError
        If required environment variables (API keys) are not set
        
    Examples
    --------
    >>> from neo4j_text2cypher.utils.config import ConfigLoader
    >>> from neo4j_text2cypher.utils.llm_factory import create_embeddings
    >>> 
    >>> config_loader = ConfigLoader("app-config.yml")
    >>> embeddings = create_embeddings(config_loader)
    >>> vectors = await embeddings.aembed_query("sample text")
    """
    llm_config = config_loader.get_llm_config()
    
    if llm_config.provider == "openai":
        return _create_openai_embeddings()
    elif llm_config.provider == "azure_openai":
        return _create_azure_openai_embeddings()
    else:
        raise ValueError(
            f"Unsupported embeddings provider: {llm_config.provider}. "
            f"Supported providers: 'openai', 'azure_openai'"
        )


def _create_openai_embeddings() -> Embeddings:
    """
    Create OpenAI embeddings instance.
    
    Returns
    -------
    OpenAIEmbeddings
        Configured OpenAI embeddings model instance
        
    Raises
    ------
    ImportError
        If langchain-openai package is not installed
    RuntimeError
        If OPENAI_API_KEY environment variable is not set
    """
    try:
        from langchain_openai import OpenAIEmbeddings
    except ImportError as e:
        raise ImportError(
            "langchain-openai package is required for OpenAI embeddings. "
            "Install it with: pip install langchain-openai"
        ) from e
    
    # Verify API key is available (same as LLM)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY environment variable is required for OpenAI embeddings"
        )
    
    return OpenAIEmbeddings(api_key=api_key)


def _create_azure_openai_embeddings() -> Embeddings:
    """
    Create Azure OpenAI embeddings instance.
    
    Returns
    -------
    AzureOpenAIEmbeddings
        Configured Azure OpenAI embeddings model instance
        
    Raises
    ------
    ImportError
        If langchain-openai package is not installed
    RuntimeError
        If required Azure OpenAI environment variables are not set
    """
    print("Creating Azure OpenAI embeddings...")
    
    try:
        from langchain_openai import AzureOpenAIEmbeddings
    except ImportError as e:
        raise ImportError(
            "langchain-openai package is required for Azure OpenAI embeddings. "
            "Install it with: pip install langchain-openai"
        ) from e
    
    # Verify required Azure environment variables (same as LLM)
    required_env_vars = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT", 
        "AZURE_OPENAI_API_VERSION"
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        raise RuntimeError(
            f"Missing required environment variables for Azure OpenAI embeddings: {missing_vars}"
        )
    
    # Check for embeddings deployment
    embeddings_deployment = os.getenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT")
    if not embeddings_deployment:
        raise RuntimeError(
            "AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT environment variable is required for Azure OpenAI embeddings.\n"
            "\n"
            "To fix this:\n"
            "1. In Azure Portal, go to your Azure OpenAI resource\n"
            "2. Navigate to 'Model deployments' or 'Deployments'\n"
            "3. Find or create a deployment using an embedding model (e.g., text-embedding-ada-002)\n"
            "4. Copy the deployment name (not the model name)\n"
            "5. Set the environment variable: AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT=<your-deployment-name>\n"
            "\n"
            "Example: AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT=my-embeddings"
        )
    
    print(f"Using Azure embeddings deployment: {embeddings_deployment}")
    print(f"Azure endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
    
    embeddings = AzureOpenAIEmbeddings(
        deployment=embeddings_deployment,
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )
    
    print("✅ Azure OpenAI embeddings created successfully")
    return embeddings