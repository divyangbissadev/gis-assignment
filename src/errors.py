"""
Shared exception types for ArcGIS client, compliance checking, and session management.
"""

class ArcGISError(Exception):
    """Base exception for ArcGIS client failures."""

class ArcGISValidationError(ArcGISError):
    """Raised when request parameters are invalid."""

class ArcGISResponseError(ArcGISError):
    """Raised when ArcGIS service responds with an error payload."""

class ComplianceError(Exception):
    """Raised when compliance checks cannot be performed."""

class SessionManagerError(Exception):
    """Raised when session persistence fails."""

class DiscrepancyError(Exception):
    """Raised when GIS vs database discrepancy detection fails."""
