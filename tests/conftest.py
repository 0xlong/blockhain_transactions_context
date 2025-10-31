import sys
import os

# Add project root to Python path for all tests
# This file is automatically loaded by pytest before running any tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

