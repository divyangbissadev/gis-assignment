#!/usr/bin/env python3
"""
Natural Language Query Parser Demo

This script demonstrates the LLM-based NLP query parser for ArcGIS.
It shows how to convert natural language queries into ArcGIS WHERE clauses
and execute them against a real ArcGIS Feature Service.

Usage:
    python3 nlp_query_demo.py

Requirements:
    - Set ANTHROPIC_API_KEY environment variable
    - Internet connection for ArcGIS service queries
"""

import sys
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from src.arcgis_client import ArcGISClient
from src.nlp_query_parser import NLPQueryParser
from src.query_executor import execute_query as exec_advanced_query
from src.errors import ArcGISError, ArcGISValidationError


# USA Census Counties Feature Service
SERVICE_URL = os.getenv(
    'ARCGIS_SERVICE_URL',
    "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/"
    "USA_Census_Counties/FeatureServer/0"
)


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_supported_queries() -> None:
    """Display all supported query examples."""
    print_section("Supported Query Examples")

    examples = NLPQueryParser.get_supported_queries()
    for i, example in enumerate(examples, 1):
        print(f"{i}. Natural Language:")
        print(f"   \"{example['natural_language']}\"")
        print(f"\n   WHERE Clause:")
        print(f"   {example['where_clause']}")
        print(f"\n   Description: {example['description']}")
        print()


def print_field_mappings() -> None:
    """Display available field mappings."""
    print_section("Available Field Mappings")

    mappings = NLPQueryParser.get_field_mappings()
    print("Natural Language → ArcGIS Field Name")
    print("-" * 50)
    for natural, field in sorted(mappings.items()):
        print(f"  {natural:20} → {field}")
    print()


def demo_parse_query(parser: NLPQueryParser, query: str):
    """
    Parse a natural language query and display results.

    Args:
        parser: NLPQueryParser instance
        query: Natural language query string

    Returns:
        ParsedQuery object if successful, None otherwise
    """
    print(f"Query: \"{query}\"")
    print("-" * 80)

    try:
        result = parser.parse(query)

        print(f"✓ WHERE Clause: {result.where_clause}")
        if result.order_by:
            print(f"  ORDER BY: {result.order_by}")
        if result.limit:
            print(f"  LIMIT: {result.limit}")
        if result.aggregation:
            print(f"  AGGREGATION: {result.aggregation}")
        if result.spatial_filter:
            print(f"  SPATIAL FILTER: {result.spatial_filter}")
        print(f"  Confidence: {result.confidence:.2%}")
        print(f"  Explanation: {result.explanation}")
        print(f"  Detected Fields: {', '.join(result.detected_fields)}")
        print()

        return result

    except ArcGISValidationError as e:
        print(f"✗ Parse Error: {e}")
        print()
        return None
    except Exception as e:
        print(f"✗ Unexpected Error: {e}")
        print()
        return None


def execute_query(client: ArcGISClient, parsed_query) -> None:
    """
    Execute a parsed query against ArcGIS and display results.

    Args:
        client: ArcGISClient instance
        parsed_query: ParsedQuery object from parser
    """
    try:
        if parsed_query.aggregation:
            print(f"Executing aggregation query: {parsed_query.aggregation}")
        elif parsed_query.spatial_filter:
            print(f"Executing spatial query near {parsed_query.spatial_filter.get('location')}")
        else:
            print(f"Executing query: {parsed_query.where_clause}")
        print("Fetching results...")

        # Use the advanced query executor
        result = exec_advanced_query(client, parsed_query)

        if result.get('type') == 'Aggregation':
            print(f"✓ {result['aggregation']} Result: {result['result']}")
        else:
            feature_count = result.get('count', 0)
            print(f"✓ Found {feature_count} features")

            if feature_count > 0:
                # Display first few results
                features_to_show = min(5, feature_count)
                print(f"\n  Showing {features_to_show} of {feature_count} results:")

                for i, feature in enumerate(result['features'][:features_to_show], 1):
                    props = feature.get("properties", {})
                    print(f"    {i}. {props.get('NAME', 'N/A')}, {props.get('STATE_NAME', 'N/A')}")
                    print(f"       Area: {props.get('SQMI', 'N/A')} sq mi, Population: {props.get('POPULATION', 'N/A'):,}")

        print()

    except ArcGISError as e:
        print(f"✗ Query Error: {e}")
        print()
    except Exception as e:
        print(f"✗ Unexpected Error: {e}")
        print()


def interactive_mode(parser: NLPQueryParser, client: ArcGISClient) -> None:
    """Run interactive query mode."""
    print_section("Interactive Mode")
    print("Enter natural language queries (or 'quit' to exit)")
    print("Example: find counties in Texas under 2500 square miles")
    print()

    while True:
        try:
            query = input("Query: ").strip()

            if query.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break

            if not query:
                continue

            print()
            parsed_query = demo_parse_query(parser, query)

            if parsed_query:
                execute = input("\nExecute this query? (y/n): ").strip().lower()
                if execute == 'y':
                    print()
                    execute_query(client, parsed_query)

            print()

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except EOFError:
            print("\n\nGoodbye!")
            break


def main() -> None:
    """Main demo function."""
    print_section("NLP Query Parser for ArcGIS - Demo")

    # Show supported queries and field mappings
    print_supported_queries()
    print_field_mappings()

    # Initialize parser
    print_section("Initializing Parser")
    try:
        parser = NLPQueryParser(provider='gemini')
        print("✓ NLP Query Parser initialized")
        print("  Model: Claude Sonnet 4.5")
    except ArcGISValidationError as e:
        print(f"✗ Failed to initialize parser: {e}")
        print("\n  Set ANTHROPIC_API_KEY environment variable:")
        print("    export ANTHROPIC_API_KEY='your-api-key'")
        sys.exit(1)

    # Initialize ArcGIS client
    print("\n✓ ArcGIS Client initialized")
    print(f"  Service: USA Census Counties")

    # Demo queries
    print_section("Demo Queries")

    demo_queries = [
        "find top 5 counties in Texas under 2500 square miles",
        # "counties in California with population over 1 million",
        # "show me Harris county in Texas",
    ]

    client = ArcGISClient(SERVICE_URL)

    for i, query in enumerate(demo_queries, 1):
        print(f"\nDemo Query {i}:")
        print("-" * 80)
        parsed_query = demo_parse_query(parser, query)

        if parsed_query:
            execute_query(client, parsed_query)

    # Interactive mode
    try:
        response = input("\nEnter interactive mode? (y/n): ").strip().lower()
        if response == 'y':
            interactive_mode(parser, client)
    except (KeyboardInterrupt, EOFError):
        print("\n\nSkipping interactive mode.")

    print_section("Demo Complete")


if __name__ == "__main__":
    main()
