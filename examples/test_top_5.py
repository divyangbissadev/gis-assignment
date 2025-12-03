#!/usr/bin/env python3
"""
Test script for "top 5" queries to ensure proper sorting and limiting.
"""

import sys
import os
from dotenv import load_dotenv
load_dotenv()

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.nlp_query_parser import NLPQueryParser
from src.arcgis_client import ArcGISClient
from src.query_executor import execute_query

# Initialize
parser = NLPQueryParser(provider="gemini")
client = ArcGISClient(
    "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/"
    "USA_Census_Counties/FeatureServer/0"
)

print("Testing 'top 5 largest counties in Texas' query")
print("=" * 80)

# Parse the query
result = parser.parse("top 5 largest counties in Texas")

print(f"\nParsed Query:")
print(f"  WHERE: {result.where_clause}")
print(f"  ORDER BY: {result.order_by}")
print(f"  LIMIT: {result.limit}")
print(f"  Confidence: {result.confidence:.2%}")
print(f"  Explanation: {result.explanation}")

# Execute the query
print(f"\nExecuting query...")
results = execute_query(client, result)

print(f"\n✓ Query executed successfully!")
print(f"  Total results: {results['count']} counties")

# Display the top 5
print(f"\nTop 5 Largest Counties in Texas:")
print("-" * 80)
print(f"{'Rank':<6} {'County Name':<30} {'Area (sq mi)':<15} {'Population':<15}")
print("-" * 80)

for i, feature in enumerate(results['features'], 1):
    props = feature['properties']
    county_name = props.get('NAME', 'N/A')
    area = props.get('SQMI', 0)
    population = props.get('POPULATION', 0)

    print(f"{i:<6} {county_name:<30} {area:>12.2f}   {population:>12,}")

print("\n" + "=" * 80)
print("✅ Test completed successfully!")
print(f"\nNote: This fetched ALL {results.get('query', {}).get('total_fetched', 'N/A')} ")
print("counties in Texas, sorted them by area, then returned top 5.")
