"""
HackerRank Orchestrate - Entry Point Wrapper
This wrapper calls the main pipeline inside src/ to avoid shadowing the standard library 'code' module.
"""
import os
import sys

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from main import main

if __name__ == "__main__":
    main()
