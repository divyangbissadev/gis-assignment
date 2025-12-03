import hashlib
import json
import time
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.config import get_config
from src.errors import ArcGISError, ArcGISResponseError, ArcGISValidationError
from src.logger import get_logger

logger = get_logger(__name__)


class SimpleArcGISClient:
    """
    Lightweight ArcGIS Feature Service client with validation, pagination, and
    optional spatial filters. Provides lower-level access and GeoJSON helpers.

    Features:
    - Automatic retry with exponential backoff
    - Connection pooling for improved performance
    - Structured logging for observability
    - Configurable timeouts and limits
    - Request caching support
    """

    def __init__(
        self,
        service_url: str,
        session: Optional[requests.Session] = None,
        enable_cache: bool = True,
        cache_ttl: int = 300
    ) -> None:
        """
        Initialize the client.

        Args:
            service_url: Base URL of the ArcGIS Feature Service.
            session: Optional custom requests session. If not provided, a
                    session with retry logic and connection pooling is created.
            enable_cache: Enable query result caching. Default: True.
            cache_ttl: Cache time-to-live in seconds. Default: 300 (5 minutes).
        """
        self.service_url = service_url.rstrip("/")
        self.config = get_config()
        self._session = session or self._create_session()

        # Cache configuration
        self.enable_cache = enable_cache
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Tuple[Dict[str, Any], float]] = {}  # {cache_key: (result, timestamp)}
        self._cache_hits = 0
        self._cache_misses = 0

        logger.info(
            "ArcGIS client initialized",
            extra={
                "service_url": self.service_url,
                "cache_enabled": enable_cache,
                "cache_ttl": cache_ttl
            }
        )

    def _create_session(self) -> requests.Session:
        """
        Create a requests session with retry logic and connection pooling.

        Returns:
            Configured requests Session instance.
        """
        session = requests.Session()

        retry_strategy = Retry(
            total=self.config.network.max_retries,
            backoff_factor=self.config.network.retry_backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
            raise_on_status=False,
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=self.config.network.max_connections,
            pool_maxsize=self.config.network.max_connections,
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        logger.debug(
            "HTTP session created with retry and pooling",
            extra={
                "max_retries": self.config.network.max_retries,
                "pool_connections": self.config.network.max_connections,
            }
        )

        return session

    def close(self) -> None:
        """Close the HTTP session and release connections."""
        if self._session:
            self._session.close()
            logger.info("HTTP session closed")

    def __enter__(self) -> "SimpleArcGISClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - cleanup resources."""
        self.close()

    def query_features(
        self,
        where_clause: str = "1=1",
        max_records: int = 1000,
        out_fields: str = "*",
        return_geometry: bool = True,
        geometry: Optional[Dict[str, Any]] = None,
        geometry_type: Optional[str] = None,
        spatial_relationship: Optional[str] = None,
        distance: Optional[float] = None,
        units: str = "esriSRUnit_StatuteMile",
        paginate: bool = True,
        max_pages: Optional[int] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Query features from ArcGIS Feature Service with strict validation, optional
        spatial filters, pagination, aggregation across pages, and caching.

        Args:
            where_clause: SQL WHERE clause (e.g., "STATE_NAME = 'Texas'").
            max_records: Page size for ArcGIS `resultRecordCount`.
            out_fields: Comma-separated list of fields to return.
            return_geometry: Whether to include geometry in responses (required for GeoJSON).
            geometry: Optional geometry dictionary (ArcGIS format) for spatial queries.
            geometry_type: ArcGIS geometry type (e.g., "esriGeometryPoint", "esriGeometryPolygon").
            spatial_relationship: ArcGIS spatial relationship (e.g., "esriSpatialRelWithin").
            distance: Buffer distance for spatial queries (used with point geometry).
            units: Distance units (defaults to statute miles).
            paginate: When True, automatically traverse pages using resultOffset until exhausted.
            max_pages: Maximum number of pages to retrieve. None means unlimited (default: None).
                      Useful as a safety limit to prevent runaway queries or memory exhaustion.
            use_cache: Whether to use cached results if available. Default: True.

        Returns:
            Dictionary containing the query response (JSON).

        Raises:
            ArcGISValidationError: When provided arguments are invalid.
            ArcGISResponseError: When the service responds with an error payload.
            ArcGISError: For network failures or unexpected responses.
        """
        # Generate cache key from query parameters
        cache_key = self._generate_cache_key(
            where_clause, max_records, out_fields, return_geometry,
            geometry, geometry_type, spatial_relationship, distance, units,
            paginate, max_pages
        )

        # Check cache if enabled
        if use_cache and self.enable_cache:
            cached_result = self._get_from_cache(cache_key)
            if cached_result is not None:
                self._cache_hits += 1
                logger.info(
                    "Cache HIT",
                    extra={
                        "cache_key": cache_key[:16] + "...",
                        "where_clause": where_clause,
                        "cache_hits": self._cache_hits,
                        "cache_misses": self._cache_misses,
                        "hit_rate": f"{self._get_hit_rate():.1%}"
                    }
                )
                return cached_result
            else:
                self._cache_misses += 1
                logger.info(
                    "Cache MISS",
                    extra={
                        "cache_key": cache_key[:16] + "...",
                        "where_clause": where_clause,
                        "cache_hits": self._cache_hits,
                        "cache_misses": self._cache_misses,
                        "hit_rate": f"{self._get_hit_rate():.1%}"
                    }
                )
        logger.info(
            "Starting feature query",
            extra={
                "where_clause": where_clause,
                "max_records": max_records,
                "paginate": paginate,
                "max_pages": max_pages,
                "spatial_query": geometry is not None,
            }
        )

        if not isinstance(where_clause, str) or not where_clause.strip():
            logger.error("Invalid where_clause parameter")
            raise ArcGISValidationError("where_clause must be a non-empty string.")
        if not isinstance(max_records, int) or max_records <= 0:
            logger.error("Invalid max_records parameter", extra={"max_records": max_records})
            raise ArcGISValidationError("max_records must be a positive integer.")
        if not isinstance(out_fields, str) or not out_fields.strip():
            logger.error("Invalid out_fields parameter")
            raise ArcGISValidationError("out_fields must be a non-empty string.")
        if distance is not None and (not isinstance(distance, (int, float)) or distance <= 0):
            logger.error("Invalid distance parameter", extra={"distance": distance})
            raise ArcGISValidationError("distance must be a positive number when provided.")
        if geometry is not None and not isinstance(geometry, dict):
            logger.error("Invalid geometry parameter")
            raise ArcGISValidationError("geometry must be a dictionary in ArcGIS format.")
        if max_pages is not None and (not isinstance(max_pages, int) or max_pages <= 0):
            logger.error("Invalid max_pages parameter", extra={"max_pages": max_pages})
            raise ArcGISValidationError("max_pages must be a positive integer when provided.")

        base_params: Dict[str, Any] = {
            "f": "geojson",
            "where": where_clause,
            "outFields": out_fields,
            "returnGeometry": str(return_geometry).lower(),
            "resultRecordCount": max_records,
        }

        if geometry:
            base_params["geometry"] = json.dumps(geometry)
            base_params["geometryType"] = geometry_type or "esriGeometryPoint"
        if spatial_relationship:
            base_params["spatialRel"] = spatial_relationship
        if distance:
            base_params["distance"] = distance
            base_params["units"] = units

        start_time = time.time()
        offset = 0
        combined_features: List[Dict[str, Any]] = []
        first_response: Optional[Dict[str, Any]] = None
        page_count = 0
        max_pages_reached = False

        while True:
            page_params = dict(base_params, resultOffset=offset)
            response_data = self._execute_query(page_params)
            page_count += 1

            if first_response is None:
                first_response = {k: v for k, v in response_data.items() if k != "features"}

            features = response_data.get("features", [])
            if not isinstance(features, list):
                logger.error("Invalid features field in response")
                raise ArcGISError("ArcGIS response 'features' field is not a list.")

            combined_features.extend(features)

            logger.debug(
                "Page retrieved",
                extra={
                    "page_number": page_count,
                    "features_in_page": len(features),
                    "total_features": len(combined_features),
                    "offset": offset,
                }
            )

            if not paginate:
                break

            # Check if max_pages limit reached
            if max_pages is not None and page_count >= max_pages:
                max_pages_reached = True
                logger.warning(
                    "Maximum page limit reached",
                    extra={
                        "max_pages": max_pages,
                        "features_retrieved": len(combined_features),
                        "note": "Query may have more results - increase max_pages or remove limit"
                    }
                )
                break

            exceeded_limit = response_data.get("exceededTransferLimit", False)
            if not exceeded_limit or not features:
                break

            offset += max_records

        if first_response is None:
            first_response = {}

        aggregated = dict(first_response)
        aggregated["features"] = combined_features
        aggregated["resultCount"] = len(combined_features)

        # Add metadata about pagination limits
        if max_pages_reached:
            aggregated["maxPagesReached"] = True
            aggregated["partialResults"] = True

        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "Feature query completed",
            extra={
                "total_features": len(combined_features),
                "pages": page_count,
                "duration_ms": duration_ms,
                "max_pages_reached": max_pages_reached,
                "partial_results": max_pages_reached,
            }
        )

        # Cache the result if caching is enabled
        if self.enable_cache:
            self._add_to_cache(cache_key, aggregated)
            logger.debug(
                "Result cached",
                extra={
                    "cache_key": cache_key[:16] + "...",
                    "cache_size": len(self._cache),
                    "feature_count": len(combined_features)
                }
            )

        return aggregated

    def _execute_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single ArcGIS query request and return parsed JSON.

        Raises:
            ArcGISResponseError: When the service returns an error payload.
            ArcGISError: For transport errors or malformed responses.
        """
        url = f"{self.service_url}/query"
        request_start = time.time()

        logger.debug(
            "Executing query request",
            extra={"url": url, "params_keys": list(params.keys())}
        )

        try:
            response = self._session.get(
                url,
                params=params,
                timeout=(
                    self.config.network.connect_timeout,
                    self.config.network.read_timeout,
                ),
            )
            response.raise_for_status()

            request_duration = (time.time() - request_start) * 1000
            logger.debug(
                "Request completed",
                extra={
                    "status_code": response.status_code,
                    "duration_ms": request_duration,
                    "content_length": len(response.content),
                }
            )

        except requests.exceptions.Timeout as e:
            logger.error(
                "Request timeout",
                extra={
                    "url": url,
                    "connect_timeout": self.config.network.connect_timeout,
                    "read_timeout": self.config.network.read_timeout,
                }
            )
            raise ArcGISError(f"Request timeout: {e}") from e

        except requests.exceptions.ConnectionError as e:
            logger.error("Connection error", extra={"url": url, "error": str(e)})
            raise ArcGISError(f"Connection failed: {e}") from e

        except requests.exceptions.RequestException as e:
            logger.error("Request failed", extra={"url": url, "error": str(e)})
            raise ArcGISError(f"Failed to query features: {e}") from e

        try:
            data = response.json()
            with open('output.json', 'w', encoding='utf-8') as f:
                f.write(json.dumps(data, indent=4))
        except json.JSONDecodeError as e:
            logger.error(
                "Invalid JSON response",
                extra={
                    "status_code": response.status_code,
                    "content_preview": response.text[:200],
                }
            )
            raise ArcGISError(
                f"Received non-JSON response with status {response.status_code}"
            ) from e

        if isinstance(data, dict) and data.get("error"):
            error = data["error"]
            message = error.get("message", "ArcGIS service returned an error.")
            details: List[str] = error.get("details", [])
            detail_msg = "; ".join(details) if details else ""
            combined_message = f"{message} {detail_msg}".strip()

            logger.error(
                "ArcGIS service error",
                extra={
                    "error_message": message,
                    "error_details": details,
                    "error_code": error.get("code"),
                }
            )
            raise ArcGISResponseError(combined_message)

        if not isinstance(data, dict) or "features" not in data:
            logger.error("Unexpected response structure", extra={"data_keys": list(data.keys()) if isinstance(data, dict) else "not_dict"})
            raise ArcGISError("Unexpected response structure from ArcGIS service.")

        return data

    @staticmethod
    def to_geojson(features: List[Dict[str, Any]], spatial_reference: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Convert ArcGIS features to a GeoJSON FeatureCollection.

        Args:
            features: List of ArcGIS feature dictionaries.
            spatial_reference: Optional spatial reference to copy onto the GeoJSON metadata.

        Returns:
            GeoJSON FeatureCollection as a dictionary.
        """
        if not isinstance(features, list):
            raise ArcGISValidationError("features must be provided as a list.")

        geojson_features = []
        for feature in features:
            attrs = feature.get("attributes", {}) if isinstance(feature, dict) else {}
            geometry = feature.get("geometry", {}) if isinstance(feature, dict) else {}
            geojson_geometry = SimpleArcGISClient._arcgis_geometry_to_geojson(geometry)

            geojson_features.append({
                "type": "Feature",
                "geometry": geojson_geometry,
                "properties": attrs,
            })

        collection: Dict[str, Any] = {"type": "FeatureCollection", "features": geojson_features}
        if spatial_reference:
            collection["crs"] = {"type": "name", "properties": {"name": str(spatial_reference)}}
        return collection

    def _generate_cache_key(self, *args, **kwargs) -> str:
        """
        Generate a unique cache key from query parameters.

        Returns:
            MD5 hash of the query parameters.
        """
        # Create a deterministic string from all parameters
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_string = "|".join(key_parts)

        # Generate MD5 hash
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get a cached query result if it exists and hasn't expired.

        Args:
            cache_key: Cache key to lookup.

        Returns:
            Cached result or None if not found/expired.
        """
        if cache_key not in self._cache:
            return None

        result, timestamp = self._cache[cache_key]

        # Check if cache entry has expired
        if time.time() - timestamp > self.cache_ttl:
            del self._cache[cache_key]
            logger.debug(
                "Cache entry expired",
                extra={"cache_key": cache_key[:16] + "..."}
            )
            return None

        return result

    def _add_to_cache(self, cache_key: str, result: Dict[str, Any]) -> None:
        """
        Add a query result to the cache.

        Args:
            cache_key: Cache key.
            result: Query result to cache.
        """
        self._cache[cache_key] = (result, time.time())

    def _get_hit_rate(self) -> float:
        """
        Calculate cache hit rate.

        Returns:
            Cache hit rate as a float (0.0 to 1.0).
        """
        total = self._cache_hits + self._cache_misses
        if total == 0:
            return 0.0
        return self._cache_hits / total

    def clear_cache(self) -> None:
        """Clear all cached query results."""
        cache_size = len(self._cache)
        self._cache.clear()
        logger.info(
            "Cache cleared",
            extra={
                "entries_cleared": cache_size,
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses
            }
        )

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics.
        """
        current_time = time.time()

        valid_entries = sum(
            1 for _, (_, timestamp) in self._cache.items()
            if current_time - timestamp <= self.cache_ttl
        )

        return {
            "enabled": self.enable_cache,
            "ttl_seconds": self.cache_ttl,
            "total_entries": len(self._cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self._cache) - valid_entries,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": self._get_hit_rate(),
            "total_requests": self._cache_hits + self._cache_misses,
        }

    @staticmethod
    def _arcgis_geometry_to_geojson(geometry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Translate a subset of ArcGIS geometry types to GeoJSON."""
        if not geometry:
            return None

        if "x" in geometry and "y" in geometry:
            return {"type": "Point", "coordinates": [geometry["x"], geometry["y"]]}

        if "rings" in geometry:
            return {"type": "Polygon", "coordinates": geometry["rings"]}

        if "paths" in geometry:
            paths = geometry["paths"]
            if not paths:
                return None
            if len(paths) == 1:
                return {"type": "LineString", "coordinates": paths[0]}
            return {"type": "MultiLineString", "coordinates": paths}

        return None


class ArcGISClient(SimpleArcGISClient):
    """
    Convenience facade that returns GeoJSON FeatureCollections by default and exposes
    simple attribute and nearby (spatial) query helpers.
    """

    def query(self, where: str = "1=1", out_fields: str = "*", page_size: int = 1000, paginate: bool = True, max_pages: Optional[int] = None) -> Dict[str, Any]:
        """
        Attribute-based query that returns GeoJSON.

        Args:
            where: SQL WHERE clause (e.g., "STATE_NAME = 'Texas'").
            out_fields: Comma-separated list of fields to return.
            page_size: Number of features per page.
            paginate: Whether to automatically fetch all pages.
            max_pages: Maximum number of pages to retrieve (None = unlimited).

        Returns:
            GeoJSON FeatureCollection with metadata.
        """
        data = super().query_features(
            where_clause=where,
            max_records=page_size,
            out_fields=out_fields,
            return_geometry=True,
            paginate=paginate,
            max_pages=max_pages,
        )

        result = self.to_geojson(data["features"], spatial_reference=data.get("spatialReference"))

        # Preserve pagination metadata
        if data.get("maxPagesReached"):
            result["maxPagesReached"] = True
            result["partialResults"] = True

        return result

    def query_nearby(
        self,
        point: Tuple[float, float],
        distance_miles: float,
        where: str = "1=1",
        out_fields: str = "*",
        page_size: int = 1000,
        paginate: bool = True,
        spatial_relationship: str = "esriSpatialRelIntersects",
        max_pages: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Spatial query within a given distance (miles) of a point; returns GeoJSON.

        Args:
            point: (longitude, latitude) tuple.
            distance_miles: Buffer distance in miles.
            where: SQL WHERE clause for additional filtering.
            out_fields: Comma-separated list of fields to return.
            page_size: Number of features per page.
            paginate: Whether to automatically fetch all pages.
            spatial_relationship: ArcGIS spatial relationship type.
            max_pages: Maximum number of pages to retrieve (None = unlimited).

        Returns:
            GeoJSON FeatureCollection with metadata.
        """
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            raise ArcGISValidationError("point must be a 2-tuple of (x, y).")

        geometry = {"x": point[0], "y": point[1], "spatialReference": {"wkid": 4326}}

        data = super().query_features(
            where_clause=where,
            max_records=page_size,
            out_fields=out_fields,
            return_geometry=True,
            geometry=geometry,
            geometry_type="esriGeometryPoint",
            spatial_relationship=spatial_relationship,
            distance=distance_miles,
            units="esriSRUnit_StatuteMile",
            paginate=paginate,
            max_pages=max_pages,
        )

        result = self.to_geojson(data["features"], spatial_reference=data.get("spatialReference"))

        # Preserve pagination metadata
        if data.get("maxPagesReached"):
            result["maxPagesReached"] = True
            result["partialResults"] = True

        return result
