"""
Query Executor for Advanced NLP Queries.

This module provides helpers to execute ParsedQuery objects with advanced features
like ORDER BY, LIMIT, aggregations, and spatial filters.
"""

from typing import Dict, Any, List, Optional, Tuple
from src.nlp_query_parser import ParsedQuery
from src.arcgis_client import ArcGISClient
from src.logger import get_logger

logger = get_logger(__name__)


# Common city coordinates for spatial queries
CITY_COORDINATES = {
    "austin, texas": (-97.7431, 30.2672),
    "houston, texas": (-95.3698, 29.7604),
    "dallas, texas": (-96.7970, 32.7767),
    "san antonio, texas": (-98.4936, 29.4241),
    "los angeles, california": (-118.2437, 34.0522),
    "san francisco, california": (-122.4194, 37.7749),
    "new york, new york": (-74.0060, 40.7128),
    "chicago, illinois": (-87.6298, 41.8781),
    "phoenix, arizona": (-112.0740, 33.4484),
    "philadelphia, pennsylvania": (-75.1652, 39.9526),
}


class QueryExecutor:
    """
    Execute advanced NLP queries with ORDER BY, LIMIT, aggregations, and spatial filters.
    """

    def __init__(self, client: ArcGISClient):
        """
        Initialize the query executor.

        Args:
            client: ArcGIS client instance to use for queries.
        """
        self.client = client

    def execute(self, parsed_query: ParsedQuery, max_results: int = 1000) -> Dict[str, Any]:
        """
        Execute a parsed query with all advanced features.

        Args:
            parsed_query: ParsedQuery object from NLPQueryParser.
            max_results: Maximum number of results to return. Default: 1000.

        Returns:
            Dictionary with results and metadata.
        """
        logger.info(
            "Executing parsed query",
            extra={
                "where_clause": parsed_query.where_clause,
                "has_order_by": parsed_query.order_by is not None,
                "has_limit": parsed_query.limit is not None,
                "has_aggregation": parsed_query.aggregation is not None,
                "has_spatial": parsed_query.spatial_filter is not None,
            }
        )

        # Handle aggregation queries
        if parsed_query.aggregation:
            return self._execute_aggregation(parsed_query)

        # Handle spatial queries
        if parsed_query.spatial_filter:
            return self._execute_spatial_query(parsed_query, max_results)

        # Handle regular queries with optional ORDER BY and LIMIT
        return self._execute_regular_query(parsed_query, max_results)

    def _execute_regular_query(
        self,
        parsed_query: ParsedQuery,
        max_results: int
    ) -> Dict[str, Any]:
        """Execute a regular query with optional ORDER BY and LIMIT."""
        # If we have ORDER BY, we need ALL results to sort correctly
        # Otherwise, we might miss the "top N" if they're on later pages
        if parsed_query.order_by:
            # Fetch all results (no page limit)
            result = self.client.query(
                where=parsed_query.where_clause,
                page_size=1000,
                max_pages=None  # Fetch all pages
            )
        else:
            # For non-sorted queries, we can limit pages
            result = self.client.query(
                where=parsed_query.where_clause,
                page_size=min(max_results, 1000),
                max_pages=None  # Still get all results
            )

        features = result.get("features", [])

        # Apply ORDER BY if specified
        if parsed_query.order_by:
            features = self._apply_order_by(features, parsed_query.order_by)

        # Apply LIMIT if specified
        if parsed_query.limit:
            features = features[:parsed_query.limit]

        return {
            "type": "FeatureCollection",
            "features": features,
            "count": len(features),
            "query": {
                "where_clause": parsed_query.where_clause,
                "order_by": parsed_query.order_by,
                "limit": parsed_query.limit,
            },
            "explanation": parsed_query.explanation,
            "confidence": parsed_query.confidence,
        }

    def _execute_aggregation(self, parsed_query: ParsedQuery) -> Dict[str, Any]:
        """Execute an aggregation query (COUNT, SUM, AVG)."""
        # For COUNT, just get all features and count them
        result = self.client.query(
            where=parsed_query.where_clause,
            page_size=1000
        )

        features = result.get("features", [])
        count = len(features)

        aggregation_type = parsed_query.aggregation.upper()

        if aggregation_type == "COUNT":
            return {
                "type": "Aggregation",
                "aggregation": "COUNT",
                "result": count,
                "query": {
                    "where_clause": parsed_query.where_clause,
                },
                "explanation": parsed_query.explanation,
                "confidence": parsed_query.confidence,
            }

        # For SUM/AVG, we'd need to know which field to aggregate
        # This could be enhanced further
        return {
            "type": "Aggregation",
            "aggregation": aggregation_type,
            "result": count,
            "note": f"{aggregation_type} aggregation implemented as COUNT for now",
            "query": {
                "where_clause": parsed_query.where_clause,
            },
            "explanation": parsed_query.explanation,
            "confidence": parsed_query.confidence,
        }

    def _execute_spatial_query(
        self,
        parsed_query: ParsedQuery,
        max_results: int
    ) -> Dict[str, Any]:
        """Execute a spatial proximity query."""
        spatial_filter = parsed_query.spatial_filter

        if spatial_filter.get("type") == "point":
            location = spatial_filter.get("location", "").lower()
            distance_miles = spatial_filter.get("distance_miles", 50)

            # Look up coordinates
            point = self._get_coordinates(location)

            if not point:
                logger.warning(
                    f"Could not find coordinates for location: {location}"
                )
                # Fall back to regular query
                return self._execute_regular_query(parsed_query, max_results)

            # Execute spatial query
            # If we have ORDER BY, fetch all results
            if parsed_query.order_by:
                result = self.client.query_nearby(
                    point=point,
                    distance_miles=distance_miles,
                    where=parsed_query.where_clause,
                    page_size=1000,
                    max_pages=None  # Fetch all pages for sorting
                )
            else:
                result = self.client.query_nearby(
                    point=point,
                    distance_miles=distance_miles,
                    where=parsed_query.where_clause,
                    page_size=min(max_results, 1000),
                    max_pages=None
                )

            features = result.get("features", [])

            # Apply ORDER BY if specified
            if parsed_query.order_by:
                features = self._apply_order_by(features, parsed_query.order_by)

            # Apply LIMIT if specified
            if parsed_query.limit:
                features = features[:parsed_query.limit]

            return {
                "type": "FeatureCollection",
                "features": features,
                "count": len(features),
                "query": {
                    "where_clause": parsed_query.where_clause,
                    "spatial_filter": spatial_filter,
                    "order_by": parsed_query.order_by,
                    "limit": parsed_query.limit,
                },
                "explanation": parsed_query.explanation,
                "confidence": parsed_query.confidence,
            }

        # Unknown spatial filter type
        return self._execute_regular_query(parsed_query, max_results)

    def _apply_order_by(self, features: List[Dict], order_by: str) -> List[Dict]:
        """
        Apply ORDER BY to features.

        Args:
            features: List of feature dictionaries.
            order_by: ORDER BY clause (e.g., "SQMI DESC").

        Returns:
            Sorted list of features.
        """
        parts = order_by.split()
        if len(parts) < 1:
            return features

        field_name = parts[0]
        direction = parts[1].upper() if len(parts) > 1 else "ASC"

        reverse = direction == "DESC"

        # Sort by the specified field
        def get_sort_key(feature):
            value = feature.get("properties", {}).get(field_name)
            if value is None:
                return 0 if isinstance(value, (int, float)) else ""
            return value

        try:
            return sorted(features, key=get_sort_key, reverse=reverse)
        except Exception as e:
            logger.warning(f"Failed to sort features: {e}")
            return features

    def _get_coordinates(self, location: str) -> Optional[Tuple[float, float]]:
        """
        Get coordinates for a location name.

        Args:
            location: Location name (e.g., "Austin, Texas").

        Returns:
            Tuple of (longitude, latitude) or None if not found.
        """
        location = location.lower().strip()

        # Check predefined coordinates
        if location in CITY_COORDINATES:
            return CITY_COORDINATES[location]

        # Try variations
        for city, coords in CITY_COORDINATES.items():
            if location in city or city in location:
                return coords

        return None


def execute_query(
    client: ArcGISClient,
    parsed_query: ParsedQuery,
    max_results: int = 1000
) -> Dict[str, Any]:
    """
    Convenience function to execute a parsed query.

    Args:
        client: ArcGIS client instance.
        parsed_query: ParsedQuery object from NLPQueryParser.
        max_results: Maximum number of results to return.

    Returns:
        Dictionary with results and metadata.
    """
    executor = QueryExecutor(client)
    return executor.execute(parsed_query, max_results)
