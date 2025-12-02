#!/usr/bin/env python3
"""
Multi-Provider NLP Query Parser Demo

Demonstrates using multiple LLM providers (Anthropic, OpenAI, Gemini) for parsing
natural language queries into ArcGIS WHERE clauses.

Usage:
    python3 multi_provider_demo.py

Requirements:
    - Set at least one of: ANTHROPIC_API_KEY, OPENAI_API_KEY, or GEMINI_API_KEY
    - Internet connection for API calls
"""

import sys
import os
from typing import Optional, List
from dotenv import load_dotenv

from src.nlp_query_parser import NLPQueryParser
from src.errors import ArcGISValidationError

# Load environment variables
load_dotenv()


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def check_provider_availability() -> List[str]:
    """
    Check which providers have API keys configured.

    Returns:
        List of available provider names.
    """
    available = []

    if os.environ.get("ANTHROPIC_API_KEY"):
        available.append("anthropic")
    if os.environ.get("OPENAI_API_KEY"):
        available.append("openai")
    if os.environ.get("GEMINI_API_KEY"):
        available.append("gemini")

    return available


def display_provider_info() -> None:
    """Display information about all supported providers."""
    print_section("Supported LLM Providers")

    providers = NLPQueryParser.get_available_providers()

    for name, info in providers.items():
        env_var = info['env_var']
        is_configured = "✓" if os.environ.get(env_var) else "✗"

        print(f"{is_configured} {info['name']}")
        print(f"   Default Model: {info['default_model']}")
        print(f"   Environment Variable: {env_var}")
        print(f"   Sign Up: {info['signup_url']}")
        print(f"   Available Models:")
        for model in info['models']:
            print(f"     - {model}")
        print()


def test_provider(provider_name: str, query: str) -> Optional[dict]:
    """
    Test a specific provider with a query.

    Args:
        provider_name: Name of the provider to test.
        query: Natural language query to parse.

    Returns:
        Parsed result dict or None if failed.
    """
    try:
        print(f"\n{provider_name.upper()}")
        print("-" * 60)

        parser = NLPQueryParser(provider=provider_name)

        result = parser.parse(query)

        print(f"✓ Success")
        print(f"  WHERE Clause: {result.where_clause}")
        print(f"  Confidence: {result.confidence:.2%}")
        print(f"  Explanation: {result.explanation}")
        print(f"  Detected Fields: {', '.join(result.detected_fields)}")

        return {
            "provider": provider_name,
            "where_clause": result.where_clause,
            "confidence": result.confidence
        }

    except ArcGISValidationError as e:
        print(f"✗ Error: {e}")
        return None
    except Exception as e:
        print(f"✗ Unexpected Error: {e}")
        return None


def compare_providers(query: str, providers: List[str]) -> None:
    """
    Compare results from multiple providers for the same query.

    Args:
        query: Natural language query to test.
        providers: List of provider names to compare.
    """
    print_section(f"Comparing Providers: '{query}'")

    results = []
    for provider in providers:
        result = test_provider(provider, query)
        if result:
            results.append(result)

    if len(results) > 1:
        print("\n" + "=" * 60)
        print("COMPARISON SUMMARY")
        print("=" * 60)

        # Check if all providers agree
        where_clauses = [r['where_clause'] for r in results]
        if len(set(where_clauses)) == 1:
            print("\n✓ All providers generated the same WHERE clause:")
            print(f"  {where_clauses[0]}")
        else:
            print("\n⚠ Providers generated different WHERE clauses:")
            for result in results:
                print(f"\n  {result['provider'].upper()}:")
                print(f"    {result['where_clause']}")
                print(f"    Confidence: {result['confidence']:.2%}")


def interactive_provider_selection() -> Optional[str]:
    """
    Let user select a provider interactively.

    Returns:
        Selected provider name or None if cancelled.
    """
    available = check_provider_availability()

    if not available:
        print("✗ No providers configured. Please set at least one API key.")
        return None

    print("\nAvailable Providers:")
    for i, provider in enumerate(available, 1):
        providers_info = NLPQueryParser.get_available_providers()
        print(f"  {i}. {providers_info[provider]['name']} ({provider})")

    try:
        choice = input("\nSelect provider (1-{}): ".format(len(available))).strip()
        idx = int(choice) - 1

        if 0 <= idx < len(available):
            return available[idx]
        else:
            print("Invalid selection")
            return None

    except (ValueError, KeyboardInterrupt, EOFError):
        return None


def main() -> None:
    """Main demo function."""
    print_section("Multi-Provider NLP Query Parser Demo")

    # Display provider information
    display_provider_info()

    # Check available providers
    available = check_provider_availability()

    if not available:
        print("=" * 80)
        print("⚠ NO PROVIDERS CONFIGURED")
        print("=" * 80)
        print("\nPlease set at least one API key in your environment:")
        print("\n  export ANTHROPIC_API_KEY='your-key'")
        print("  export OPENAI_API_KEY='your-key'")
        print("  export GEMINI_API_KEY='your-key'")
        print("\nOr create a .env file with the API keys.")
        print("\nSee MULTI_PROVIDER_SETUP.md for detailed instructions.")
        sys.exit(1)

    print("=" * 80)
    print(f"✓ {len(available)} Provider(s) Configured: {', '.join(available)}")
    print("=" * 80)

    # Demo queries
    demo_queries = [
        "find counties in Texas under 2500 square miles",
        "counties in California with population over 1 million",
        "show me Harris county in Texas",
    ]

    # Test all available providers with first query
    if len(available) > 1:
        print_section("Comparing All Providers")
        compare_providers(demo_queries[0], available)

    # Test each query with first available provider
    print_section(f"Testing Queries with {available[0].upper()}")

    for i, query in enumerate(demo_queries, 1):
        print(f"\nQuery {i}: \"{query}\"")
        print("-" * 60)
        test_provider(available[0], query)

    # Interactive mode
    print_section("Interactive Mode")

    try:
        response = input("Enter interactive mode? (y/n): ").strip().lower()
        if response == 'y':
            selected_provider = interactive_provider_selection()

            if selected_provider:
                parser = NLPQueryParser(provider=selected_provider)
                providers_info = NLPQueryParser.get_available_providers()
                print(f"\n✓ Using {providers_info[selected_provider]['name']}")
                print("\nEnter natural language queries (or 'quit' to exit)")
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
                        result = parser.parse(query)
                        print(f"✓ WHERE Clause: {result.where_clause}")
                        print(f"  Confidence: {result.confidence:.2%}")
                        print(f"  Explanation: {result.explanation}")
                        print()

                    except KeyboardInterrupt:
                        print("\n\nGoodbye!")
                        break
                    except EOFError:
                        print("\n\nGoodbye!")
                        break
                    except Exception as e:
                        print(f"✗ Error: {e}\n")

    except (KeyboardInterrupt, EOFError):
        print("\n\nSkipping interactive mode.")

    print_section("Demo Complete")
    print("See MULTI_PROVIDER_SETUP.md for more information on provider setup.")


if __name__ == "__main__":
    main()
