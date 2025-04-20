#!/usr/bin/env python3
# This script exports the project directory to JSON, ignoring .gitignore patterns.
# Usage:
#     pip install pathspec
#     python export_project.py > project.json

import os
import sys
import json

try:
    from pathspec import PathSpec
except ImportError:
    sys.exit("Missing dependency: pip install pathspec")

# Load .gitignore patterns
gitignore_path = os.path.join(os.getcwd(), '.gitignore')
if os.path.exists(gitignore_path):
    with open(gitignore_path, 'r') as f:
        patterns = [line.rstrip('\n') for line in f]
else:
    patterns = []
spec = PathSpec.from_lines('gitwildmatch', patterns)

result = {}
# Only export files in the 'scripts' directory
script_dir = os.path.join(os.getcwd(), 'scripts')
if not os.path.isdir(script_dir):
    sys.exit(f"Scripts directory not found: {script_dir}")
root_dir = script_dir

for root, dirs, files in os.walk(root_dir):
    rel_dir = os.path.relpath(root, root_dir)
    if rel_dir == '.':
        rel_dir = ''
    # Filter out ignored directories
    dirs[:] = [d for d in dirs if not spec.match_file(os.path.join(rel_dir, d))]
    for file in files:
        rel_path = os.path.normpath(os.path.join(rel_dir, file))
        if spec.match_file(rel_path):
            continue
        abs_path = os.path.join(root, file)
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except (UnicodeDecodeError, PermissionError):
            continue
        result[rel_path] = content

json.dump(result, sys.stdout, indent=2)
sys.stdout.write('\n') 