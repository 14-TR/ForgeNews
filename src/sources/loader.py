import json
import os
import importlib.util
from pathlib import Path
from typing import Dict, Any, Optional

def load_registry():
    """Load the source registry from config file."""
    config_path = Path(__file__).parent.parent.parent / "config" / "source_registry.json"
    with open(config_path, "r") as f:
        return json.load(f)

def get_source(category: str, source_id: str):
    """Dynamically load a source parser module.
    
    Args:
        category: One of the categories in source_registry (conflict, ai, markets)
        source_id: The ID of a specific source within that category
        
    Returns:
        The loaded module for that source
    """
    registry = load_registry()
    
    if category not in registry:
        raise ValueError(f"Category {category} not found in registry")
    
    for src in registry[category]:
        if src["id"] == source_id:
            # Extract the parser path and import it
            parser_path = src["parser"]
            
            # Convert to Python module path
            rel_path = parser_path.replace("/", ".").replace(".py", "")
            
            try:
                return importlib.import_module(rel_path)
            except ImportError:
                raise ImportError(f"Failed to import {rel_path}")
    
    raise ValueError(f"Source {source_id} not found in category {category}") 