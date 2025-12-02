"""
Natural Language Query Parser for ArcGIS WHERE clauses.

This module uses an LLM (supports Anthropic, OpenAI, Google Gemini) to parse
natural language queries and convert them to ArcGIS-compatible SQL WHERE clauses.

Example:
    >>> # Use Anthropic (default)
    >>> parser = NLPQueryParser()
    >>> result = parser.parse("find counties in Texas under 2500 square miles")
    >>> print(result.where_clause)
    "STATE_NAME = 'Texas' AND SQMI < 2500"

    >>> # Use OpenAI
    >>> parser = NLPQueryParser(provider="openai")

    >>> # Use Gemini
    >>> parser = NLPQueryParser(provider="gemini", model="gemini-1.5-pro")
"""

import json
import os
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from src.errors import ArcGISValidationError
from src.logger import get_logger
from src.llm_providers import create_provider, get_available_providers, BaseLLMProvider

logger = get_logger(__name__)


@dataclass
class ParsedQuery:
    """Result of parsing a natural language query."""
    where_clause: str
    confidence: float
    explanation: str
    detected_fields: List[str]
    # Advanced query features
    order_by: Optional[str] = None  # e.g., "SQMI DESC"
    limit: Optional[int] = None      # e.g., 5 for "top 5"
    aggregation: Optional[str] = None  # e.g., "COUNT" for count queries
    spatial_filter: Optional[Dict[str, Any]] = None  # Spatial query params


class NLPQueryParser:
    """
    LLM-based natural language query parser for ArcGIS queries.

    Converts natural language queries like "find counties in Texas under 2500 square miles"
    into ArcGIS WHERE clauses like "STATE_NAME = 'Texas' AND SQMI < 2500".

    Features:
    - Supports multiple LLM providers (Anthropic, OpenAI, Google Gemini)
    - Supports attribute queries (state, county, area, population)
    - Handles comparison operators (<, >, <=, >=, =, !=)
    - Supports compound queries with AND/OR
    - Provides confidence scores and explanations
    - Lists detected field names
    """

    # Common field mappings for USA Census Counties dataset
    FIELD_MAPPINGS = {
        "state": "STATE_NAME",
        "state name": "STATE_NAME",
        "county": "NAME",
        "county name": "NAME",
        "area": "SQMI",
        "square miles": "SQMI",
        "sq miles": "SQMI",
        "sqmi": "SQMI",
        "population": "POPULATION",
        "pop": "POPULATION",
        "fips": "FIPS",
        "state fips": "STATE_FIPS",
    }

    EXAMPLE_QUERIES = [
        {
            "natural_language": "find counties in Texas under 2500 square miles",
            "where_clause": "STATE_NAME = 'Texas' AND SQMI < 2500",
            "description": "Filter by state and area threshold"
        },
        {
            "natural_language": "top 5 largest counties in Texas",
            "where_clause": "STATE_NAME = 'Texas'",
            "order_by": "SQMI DESC",
            "limit": 5,
            "description": "Top N query with ORDER BY and LIMIT"
        },
        {
            "natural_language": "counties in California with population over 1 million",
            "where_clause": "STATE_NAME = 'California' AND POPULATION > 1000000",
            "description": "Combine state filter with population criteria"
        },
        {
            "natural_language": "how many counties are in Texas",
            "where_clause": "STATE_NAME = 'Texas'",
            "aggregation": "COUNT",
            "description": "Count aggregation query"
        },
        {
            "natural_language": "counties near Austin Texas within 50 miles",
            "where_clause": "1=1",
            "spatial_filter": {
                "type": "point",
                "location": "Austin, Texas",
                "distance_miles": 50
            },
            "description": "Spatial proximity query"
        },
        {
            "natural_language": "show me counties in Texas or Oklahoma",
            "where_clause": "STATE_NAME IN ('Texas', 'Oklahoma')",
            "description": "Multiple state selection with OR logic"
        },
        {
            "natural_language": "smallest 3 counties in California",
            "where_clause": "STATE_NAME = 'California'",
            "order_by": "SQMI ASC",
            "limit": 3,
            "description": "Bottom N query with ascending order"
        },
        {
            "natural_language": "counties in Texas between 1000 and 3000 square miles",
            "where_clause": "STATE_NAME = 'Texas' AND SQMI >= 1000 AND SQMI <= 3000",
            "description": "Range query with multiple conditions"
        },
    ]

    def __init__(
        self,
        provider: str = "anthropic",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        enable_cache: bool = True,
        cache_ttl: int = 3600
    ):
        """
        Initialize the NLP query parser.

        Args:
            provider: LLM provider to use ("anthropic", "openai", or "gemini"). Default: "anthropic".
            api_key: API key for the provider. If not provided, looks for environment variable.
            model: Model name to use. If not provided, uses provider default.
            enable_cache: Enable caching of parsed queries. Default: True.
            cache_ttl: Cache time-to-live in seconds. Default: 3600 (1 hour).

        Raises:
            ArcGISValidationError: If API key is not provided or provider is unsupported.

        Examples:
            >>> # Use Anthropic (default)
            >>> parser = NLPQueryParser()

            >>> # Use OpenAI with custom model
            >>> parser = NLPQueryParser(provider="openai", model="gpt-4")

            >>> # Use Gemini with API key and disable cache
            >>> parser = NLPQueryParser(provider="gemini", api_key="your-key", enable_cache=False)
        """
        self.provider = create_provider(provider=provider, api_key=api_key, model=model)
        self.provider_name = provider
        self.enable_cache = enable_cache
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, tuple] = {}  # {query: (result, timestamp)}

        logger.info(
            "NLP Query Parser initialized",
            extra={
                "provider": self.provider.provider_name,
                "model": getattr(self.provider, 'model', 'default'),
                "cache_enabled": enable_cache
            }
        )

    def parse(self, natural_query: str, use_cache: bool = True) -> ParsedQuery:
        """
        Parse a natural language query into an ArcGIS WHERE clause with advanced features.

        Args:
            natural_query: Natural language query string.
            use_cache: Whether to use cached results. Default: True.

        Returns:
            ParsedQuery object containing WHERE clause, ORDER BY, LIMIT, aggregations, and spatial filters.

        Raises:
            ArcGISValidationError: If query is empty or parsing fails.
        """
        if not natural_query or not natural_query.strip():
            raise ArcGISValidationError("Query cannot be empty")

        # Check cache
        if use_cache and self.enable_cache:
            cached = self._get_from_cache(natural_query)
            if cached:
                logger.info("Retrieved query from cache", extra={"query": natural_query})
                return cached

        logger.info("Parsing natural language query", extra={"query": natural_query})

        # Build the enhanced prompt
        prompt = self._build_prompt(natural_query)

        try:
            # Call LLM provider
            response_text = self.provider.generate(prompt, max_tokens=1536)

            # Parse the response
            result = self._parse_response(response_text)

            # Cache the result
            if self.enable_cache:
                self._add_to_cache(natural_query, result)

            logger.info(
                "Query parsed successfully",
                extra={
                    "query": natural_query,
                    "where_clause": result.where_clause,
                    "confidence": result.confidence,
                    "has_order_by": result.order_by is not None,
                    "has_limit": result.limit is not None,
                    "has_aggregation": result.aggregation is not None,
                    "has_spatial": result.spatial_filter is not None,
                }
            )

            return result

        except Exception as e:
            logger.error("Failed to parse query", extra={"query": natural_query, "error": str(e)})
            raise ArcGISValidationError(f"Failed to parse query: {e}") from e

    def _build_prompt(self, natural_query: str) -> str:
        """Build the enhanced prompt for parsing advanced queries."""
        field_mappings_str = "\n".join(
            f"  - {key}: {value}" for key, value in self.FIELD_MAPPINGS.items()
        )

        examples_str = "\n\n".join(
            f"Example {i+1}:\n"
            f"Natural Language: {ex['natural_language']}\n"
            f"WHERE Clause: {ex['where_clause']}\n"
            + (f"ORDER BY: {ex['order_by']}\n" if 'order_by' in ex else "")
            + (f"LIMIT: {ex['limit']}\n" if 'limit' in ex else "")
            + (f"Aggregation: {ex['aggregation']}\n" if 'aggregation' in ex else "")
            + (f"Spatial Filter: {json.dumps(ex['spatial_filter'])}\n" if 'spatial_filter' in ex else "")
            + f"Description: {ex['description']}"
            for i, ex in enumerate(self.EXAMPLE_QUERIES[:5])
        )

        return f"""You are an expert at converting natural language queries into ArcGIS queries with advanced features.

Dataset: USA Census Counties
Available Fields:
{field_mappings_str}

Your task: Convert the following natural language query into a structured ArcGIS query with:
1. WHERE clause (filtering conditions)
2. ORDER BY (for "top", "largest", "smallest", "highest", "lowest")
3. LIMIT (for "top N", "first N", "N largest", etc.)
4. Aggregation (for "count", "how many", "total", "average")
5. Spatial filters (for "near", "within N miles of")

Examples:
{examples_str}

IMPORTANT RULES:
1. Use ONLY the field names from the Available Fields list above
2. String values must be in single quotes (e.g., 'Texas')
3. Use proper SQL operators: =, !=, <, >, <=, >=, AND, OR, IN
4. For "top N largest", use ORDER BY field DESC with LIMIT N
5. For "smallest N", use ORDER BY field ASC with LIMIT N
6. For "how many" or "count", set aggregation to "COUNT"
7. For spatial queries like "near City", extract location and distance
8. If no ORDER BY is needed, set it to null
9. If no LIMIT is needed, set it to null
10. If no aggregation is needed, set it to null
11. If no spatial filter is needed, set it to null

Query to convert: "{natural_query}"

Respond in JSON format with the following structure:
{{
  "where_clause": "the SQL WHERE clause",
  "confidence": 0.95,
  "explanation": "brief explanation of the conversion",
  "detected_fields": ["list", "of", "field", "names"],
  "order_by": "FIELD_NAME DESC" or null,
  "limit": 5 or null,
  "aggregation": "COUNT" or "SUM" or "AVG" or null,
  "spatial_filter": {{"type": "point", "location": "City, State", "distance_miles": 50}} or null
}}

Only respond with the JSON, no other text."""

    def _parse_response(self, response_text: str) -> ParsedQuery:
        """Parse LLM's JSON response into a ParsedQuery object with advanced features."""
        try:
            # Extract JSON from response (handle potential markdown code blocks)
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            data = json.loads(response_text)

            return ParsedQuery(
                where_clause=data["where_clause"],
                confidence=float(data.get("confidence", 0.9)),
                explanation=data.get("explanation", ""),
                detected_fields=data.get("detected_fields", []),
                order_by=data.get("order_by"),
                limit=data.get("limit"),
                aggregation=data.get("aggregation"),
                spatial_filter=data.get("spatial_filter")
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.error("Failed to parse LLM response", extra={"response": response_text})
            raise ArcGISValidationError(f"Failed to parse LLM response: {e}") from e

    def _get_from_cache(self, query: str) -> Optional[ParsedQuery]:
        """Get a cached query result if it exists and hasn't expired."""
        import time

        if query not in self._cache:
            return None

        result, timestamp = self._cache[query]

        # Check if cache entry has expired
        if time.time() - timestamp > self.cache_ttl:
            del self._cache[query]
            return None

        return result

    def _add_to_cache(self, query: str, result: ParsedQuery) -> None:
        """Add a query result to the cache."""
        import time
        self._cache[query] = (result, time.time())

    def clear_cache(self) -> None:
        """Clear all cached queries."""
        self._cache.clear()
        logger.info("Query cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the query cache.

        Returns:
            Dictionary with cache statistics.
        """
        import time
        current_time = time.time()

        valid_entries = sum(
            1 for _, (_, timestamp) in self._cache.items()
            if current_time - timestamp <= self.cache_ttl
        )

        return {
            "total_entries": len(self._cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self._cache) - valid_entries,
            "cache_enabled": self.enable_cache,
            "cache_ttl": self.cache_ttl
        }

    @classmethod
    def get_supported_queries(cls) -> List[Dict[str, str]]:
        """
        Get a list of example queries that are supported.

        Returns:
            List of dictionaries with 'natural_language', 'where_clause', and 'description'.
        """
        return cls.EXAMPLE_QUERIES.copy()

    @classmethod
    def get_field_mappings(cls) -> Dict[str, str]:
        """
        Get the field name mappings used by the parser.

        Returns:
            Dictionary mapping natural language field references to ArcGIS field names.
        """
        return cls.FIELD_MAPPINGS.copy()

    @staticmethod
    def get_available_providers() -> Dict[str, Dict[str, Any]]:
        """
        Get information about available LLM providers.

        Returns:
            Dictionary with provider information including default models and env vars.
        """
        return get_available_providers()
