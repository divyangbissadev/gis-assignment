#!/usr/bin/env python3
"""Quick test of NLP Query Parser"""

import sys
import os
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.nlp_query_parser import NLPQueryParser

print("Testing NLP Query Parser...")
print("=" * 60)

# Initialize parser
parser = NLPQueryParser()
print("✓ Parser initialized successfully")

# Test a simple query
query = "find counties in Texas under 2500 square miles"
print(f"\nQuery: {query}")

result = parser.parse(query)

print(f"\n✓ Parse successful!")
print(f"  WHERE Clause: {result.where_clause}")
print(f"  Confidence: {result.confidence:.2%}")
print(f"  Explanation: {result.explanation}")
print(f"  Fields: {result.detected_fields}")

print("\n" + "=" * 60)
print("✓ Everything is working!")
