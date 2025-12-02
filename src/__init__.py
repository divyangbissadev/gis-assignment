"""
GIS Developer Take-Home - Core Source Code

This package provides tools for querying ArcGIS Feature Services and
analyzing compliance with business rules.
"""

from src.arcgis_client import ArcGISClient, SimpleArcGISClient
from src.compliance_checker import (
    analyze_oil_gas_lease_compliance,
    check_area_compliance,
    generate_shortfall_report,
)
from src.session_manager import SessionManager
from src.config import get_config, ApplicationConfig
from src.logger import get_logger
from src.discrepancy_detector import detect_area_discrepancies, seed_reference_database
from src.errors import (
    ArcGISError,
    ArcGISResponseError,
    ArcGISValidationError,
    ComplianceError,
    SessionManagerError,
    DiscrepancyError,
)

__version__ = "1.0.0"

__all__ = [
    "ArcGISClient",
    "SimpleArcGISClient",
    "analyze_oil_gas_lease_compliance",
    "check_area_compliance",
    "generate_shortfall_report",
    "SessionManager",
    "get_config",
    "Config",
    "get_logger",
    "detect_area_discrepancies",
    "seed_reference_database",
    "ArcGISError",
    "ArcGISResponseError",
    "ArcGISValidationError",
    "ComplianceError",
    "SessionManagerError",
    "DiscrepancyError",
]
