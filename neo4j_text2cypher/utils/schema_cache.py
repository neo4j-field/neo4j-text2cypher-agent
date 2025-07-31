"""Simple schema caching utility for Neo4j databases."""

import json
from pathlib import Path
from typing import Dict, Any, Optional


def load_schema_cache(database_name: str) -> Optional[str]:
    """
    Load cached schema for a database.
    
    Parameters
    ----------
    database_name : str
        The name of the Neo4j database
        
    Returns
    -------
    Optional[str]
        The cached schema string, or None if not found
    """
    # Get project root directory (go up from utils to project root)
    project_root = Path(__file__).parent.parent.parent
    cache_dir = project_root / "database_schema_cache"
    cache_file = cache_dir / f"{database_name}_schema.json"
    
    try:
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                return cache_data.get("schema")
        return None
    except:
        return None


def save_schema_cache(database_name: str, schema: str) -> None:
    """
    Save schema to cache.
    
    Parameters
    ----------
    database_name : str
        The name of the Neo4j database
    schema : str
        The schema string from Neo4jGraph.schema
    """
    try:
        # Get project root directory (go up from utils to project root)
        project_root = Path(__file__).parent.parent.parent
        cache_dir = project_root / "database_schema_cache"
        cache_dir.mkdir(exist_ok=True)
        cache_file = cache_dir / f"{database_name}_schema.json"
        
        cache_data = {
            "schema": schema
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2)
    except:
        pass  # If save fails, just continue without caching