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
            "1. Find your embeddings deployment name in one of these locations:\n"
            "   - Azure Portal > Your OpenAI Resource > Deployments\n"
            "   - Azure AI Foundry portal > My assets > Models + endpoints\n"
            "   - Direct link: https://oai.azure.com/resource/deployments\n"
            "2. Look for a deployment using an embedding model (e.g., text-embedding-ada-002)\n"
            "3. Copy the deployment name (not the model name)\n"
            "4. Set the environment variable: AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT=<your-deployment-name>\n"
            "\n"
            "Example: AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT=my-embeddings"
        )
    
    print(f"Using Azure embeddings deployment: {embeddings_deployment}")
    
    # Check for separate embeddings endpoint, fall back to main endpoint
    embeddings_endpoint = os.getenv("AZURE_OPENAI_EMBEDDINGS_ENDPOINT") or os.getenv("AZURE_OPENAI_ENDPOINT")
    if os.getenv("AZURE_OPENAI_EMBEDDINGS_ENDPOINT"):
        print(f"Using separate endpoint for embeddings: {embeddings_endpoint}")
    else:
        print(f"Using main Azure endpoint: {embeddings_endpoint}")
    
    # Check for separate embeddings API key, fall back to main API key
    embeddings_api_key = os.getenv("AZURE_OPENAI_EMBEDDINGS_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
    if os.getenv("AZURE_OPENAI_EMBEDDINGS_API_KEY"):
        print("Using separate API key for embeddings")
    
    # Check for separate embeddings API version, fall back to main API version
    embeddings_api_version = os.getenv("AZURE_OPENAI_EMBEDDINGS_API_VERSION") or os.getenv("AZURE_OPENAI_API_VERSION")
    if os.getenv("AZURE_OPENAI_EMBEDDINGS_API_VERSION"):
        print(f"Using separate API version for embeddings: {embeddings_api_version}")
    
    embeddings = AzureOpenAIEmbeddings(
        deployment=embeddings_deployment,
        api_key=embeddings_api_key,
        azure_endpoint=embeddings_endpoint,
        api_version=embeddings_api_version,
    )
    
    print("✅ Azure OpenAI embeddings created successfully")
    return embeddings