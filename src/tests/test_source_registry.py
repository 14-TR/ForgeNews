import json
import os
from pathlib import Path

def test_source_registry_has_required_fields():
    """Test that all sources in the registry have required fields."""
    # Get the path to the registry file
    registry_path = Path(__file__).parent.parent.parent / "config" / "source_registry.json"
    
    # Load the registry
    with open(registry_path, "r") as f:
        registry = json.load(f)
    
    # Check each category
    for category, sources in registry.items():
        for src in sources:
            # Check required fields
            assert "id" in src, f"Source in {category} missing 'id' field"
            assert "title" in src, f"Source {src.get('id', 'unknown')} in {category} missing 'title' field"
            assert "endpoint" in src, f"Source {src.get('id', 'unknown')} in {category} missing 'endpoint' field"
            assert "auth_env" in src, f"Source {src.get('id', 'unknown')} in {category} missing 'auth_env' field"
            assert "parser" in src, f"Source {src.get('id', 'unknown')} in {category} missing 'parser' field"
            assert "license" in src and "attribution" in src, f"Source {src.get('id', 'unknown')} in {category} missing 'license' or 'attribution' field"
            
            # Check if parser file exists
            parser_path = Path(__file__).parent.parent.parent / src["parser"]
            assert parser_path.exists(), f"Parser file {src['parser']} for source {src.get('id', 'unknown')} does not exist" 