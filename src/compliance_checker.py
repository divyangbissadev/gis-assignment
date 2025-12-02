from typing import List, Dict, Any

from src.errors import ComplianceError
from src.logger import get_logger

logger = get_logger(__name__)

def check_area_compliance(features: List[Dict[str, Any]], min_area_sq_miles: float) -> Dict[str, Any]:
    """
    Checks if features meet a minimum area requirement.

    Args:
        features: List of feature dictionaries containing 'attributes'.
        min_area_sq_miles: Minimum required area in square miles.

    Returns:
        A dictionary containing the compliance report, including invalid features.

    Raises:
        ComplianceError: If inputs are invalid.
    """
    logger.info(
        "Starting compliance check",
        extra={
            "feature_count": len(features) if isinstance(features, list) else 0,
            "min_area_sq_miles": min_area_sq_miles,
        }
    )

    if not isinstance(features, list):
        logger.error("Invalid features parameter type")
        raise ComplianceError("features must be provided as a list.")
    if min_area_sq_miles <= 0:
        logger.error("Invalid min_area_sq_miles parameter", extra={"min_area_sq_miles": min_area_sq_miles})
        raise ComplianceError("min_area_sq_miles must be greater than zero.")

    compliance_report = {
        "total_checked": 0,  # Only counts features with parseable SQMI values
        "compliant_count": 0,
        "non_compliant_count": 0,
        "invalid_features": 0,
        "details": []
    }

    if not features:
        return compliance_report

    for feature in features:
        attrs = feature.get("attributes", {}) if isinstance(feature, dict) else {}
        try:
            area = float(attrs.get("SQMI", 0))
        except (ValueError, TypeError):
            area = 0.0
            compliance_report["invalid_features"] += 1
            compliance_report["details"].append({
                "name": attrs.get("NAME", "Unknown"),
                "area": None,
                "required": min_area_sq_miles,
                "compliant": False,
                "note": "Invalid or missing SQMI value"
            })
            continue

        compliance_report["total_checked"] += 1
        name = attrs.get("NAME", "Unknown")
        is_compliant = area >= min_area_sq_miles

        if is_compliant:
            compliance_report["compliant_count"] += 1
        else:
            compliance_report["non_compliant_count"] += 1

        compliance_report["details"].append({
            "name": name,
            "area": area,
            "required": min_area_sq_miles,
            "compliant": is_compliant,
            "shortfall": max(0.0, min_area_sq_miles - area) if not is_compliant else 0.0,
            "recommendation": (
                "Consider consolidation with adjacent counties" if not is_compliant else ""
            ),
        })

    logger.info(
        "Compliance check completed",
        extra={
            "total_checked": compliance_report["total_checked"],
            "compliant_count": compliance_report["compliant_count"],
            "non_compliant_count": compliance_report["non_compliant_count"],
            "invalid_features": compliance_report["invalid_features"],
        }
    )

    return compliance_report


def generate_shortfall_report(features: List[Dict[str, Any]], min_area_sq_miles: float) -> Dict[str, Any]:
    """
    Produce a compliance report ordered by largest area shortfall first.

    Args:
        features: List of feature dictionaries containing 'attributes'.
        min_area_sq_miles: Minimum required area in square miles.

    Returns:
        The base compliance report plus a 'non_compliant_details' list sorted by
        descending shortfall.
    """
    base = check_area_compliance(features, min_area_sq_miles)
    non_compliant = [
        {
            "name": item["name"],
            "area_sq_miles": item["area"],
            "required_sq_miles": min_area_sq_miles,
            "shortfall_sq_miles": item["shortfall"],
            "recommendation": item.get("recommendation", ""),
        }
        for item in base["details"]
        if not item["compliant"]
    ]
    base["non_compliant_details"] = sorted(
        non_compliant,
        key=lambda x: x["shortfall_sq_miles"],
        reverse=True,
    )
    return base


def analyze_oil_gas_lease_compliance(
    features: List[Dict[str, Any]],
    min_area_sq_miles: float = 2500.0,
    include_geojson: bool = False
) -> Dict[str, Any]:
    """
    Analyze counties for oil & gas lease compliance based on minimum area requirements.

    This function identifies counties that are BELOW the minimum area requirement,
    calculates the shortfall for each non-compliant county, and ranks them by
    the largest gap first.

    Args:
        features: List of GeoJSON feature dictionaries containing 'properties' and optionally 'geometry'.
        min_area_sq_miles: Minimum required area in square miles for lease qualification.
                          Default is 2,500 sq miles for standard terms.
        include_geojson: Whether to include geometry in the results. Default is False.

    Returns:
        Dictionary containing:
            - summary: High-level statistics
            - non_compliant_counties: List of counties below requirement, ranked by shortfall
            - compliant_counties: List of counties meeting requirement (optional)
            - metadata: Policy information and analysis parameters

    Example:
        >>> from arcgis_client import ArcGISClient
        >>> from compliance_checker import analyze_oil_gas_lease_compliance
        >>>
        >>> client = ArcGISClient(service_url)
        >>> texas_data = client.query(where="STATE_NAME = 'Texas'")
        >>>
        >>> report = analyze_oil_gas_lease_compliance(
        ...     texas_data['features'],
        ...     min_area_sq_miles=2500.0
        ... )
        >>> print(f"Non-compliant: {report['summary']['non_compliant_count']}")
        >>> print(f"Largest shortfall: {report['non_compliant_counties'][0]}")
    """
    logger.info(
        "Starting oil & gas lease compliance analysis",
        extra={
            "feature_count": len(features) if isinstance(features, list) else 0,
            "min_area_sq_miles": min_area_sq_miles,
        }
    )

    if not isinstance(features, list):
        logger.error("Invalid features parameter type")
        raise ComplianceError("features must be provided as a list.")
    if min_area_sq_miles <= 0:
        logger.error("Invalid min_area_sq_miles parameter", extra={"min_area_sq_miles": min_area_sq_miles})
        raise ComplianceError("min_area_sq_miles must be greater than zero.")

    non_compliant_counties = []
    compliant_counties = []
    invalid_count = 0
    total_shortfall = 0.0

    for feature in features:
        # Extract properties (GeoJSON format uses 'properties', ArcGIS format uses 'attributes')
        props = feature.get("properties") or feature.get("attributes", {})
        geometry = feature.get("geometry") if include_geojson else None

        # Get county information
        county_name = props.get("NAME", "Unknown")
        state_name = props.get("STATE_NAME", "Unknown")
        population = props.get("POPULATION", 0)

        # Parse area
        try:
            area_sq_miles = float(props.get("SQMI", 0))
        except (ValueError, TypeError):
            invalid_count += 1
            logger.warning(
                "Invalid area value for county",
                extra={"county": county_name, "state": state_name}
            )
            continue

        # Check compliance
        is_compliant = area_sq_miles >= min_area_sq_miles
        shortfall = max(0.0, min_area_sq_miles - area_sq_miles)

        county_info = {
            "county_name": county_name,
            "state": state_name,
            "area_sq_miles": round(area_sq_miles, 2),
            "required_sq_miles": min_area_sq_miles,
            "compliant": is_compliant,
            "population": population,
        }

        if include_geojson and geometry:
            county_info["geometry"] = geometry

        if is_compliant:
            county_info["excess_area"] = round(area_sq_miles - min_area_sq_miles, 2)
            compliant_counties.append(county_info)
        else:
            county_info["shortfall_sq_miles"] = round(shortfall, 2)
            county_info["compliance_percentage"] = round((area_sq_miles / min_area_sq_miles) * 100, 2)
            county_info["recommendation"] = _generate_lease_recommendation(area_sq_miles, min_area_sq_miles)
            non_compliant_counties.append(county_info)
            total_shortfall += shortfall

    # Sort non-compliant counties by shortfall (largest gap first)
    non_compliant_counties.sort(key=lambda x: x["shortfall_sq_miles"], reverse=True)

    # Build comprehensive report
    report = {
        "summary": {
            "total_counties_analyzed": len(features) - invalid_count,
            "compliant_count": len(compliant_counties),
            "non_compliant_count": len(non_compliant_counties),
            "invalid_count": invalid_count,
            "compliance_rate_percentage": round(
                (len(compliant_counties) / (len(features) - invalid_count) * 100)
                if (len(features) - invalid_count) > 0 else 0,
                2
            ),
            "total_shortfall_sq_miles": round(total_shortfall, 2),
            "average_shortfall_sq_miles": round(
                total_shortfall / len(non_compliant_counties)
                if len(non_compliant_counties) > 0 else 0,
                2
            ),
        },
        "non_compliant_counties": non_compliant_counties,
        "compliant_counties": compliant_counties if include_geojson else [],
        "metadata": {
            "policy": "All oil & gas leases must be at least 2,500 square miles to qualify for standard terms",
            "minimum_area_requirement_sq_miles": min_area_sq_miles,
            "analysis_timestamp": __import__('datetime').datetime.now().isoformat(),
            "include_geometry": include_geojson,
        }
    }

    logger.info(
        "Oil & gas lease compliance analysis completed",
        extra={
            "total_analyzed": report['summary']['total_counties_analyzed'],
            "compliant": report['summary']['compliant_count'],
            "non_compliant": report['summary']['non_compliant_count'],
            "compliance_rate": report['summary']['compliance_rate_percentage'],
        }
    )

    return report


def _generate_lease_recommendation(area_sq_miles: float, min_area_sq_miles: float) -> str:
    """
    Generate lease recommendation based on area shortfall.

    Args:
        area_sq_miles: Actual area in square miles.
        min_area_sq_miles: Required minimum area.

    Returns:
        Recommendation string.
    """
    shortfall = min_area_sq_miles - area_sq_miles
    percentage = (area_sq_miles / min_area_sq_miles) * 100

    if percentage >= 90:
        return "Consider special terms negotiation - minor shortfall"
    elif percentage >= 75:
        return "Combine with adjacent tracts or apply for non-standard terms"
    elif percentage >= 50:
        return "Significant consolidation required - consider pooling agreement"
    else:
        return "Does not meet minimum requirements - alternative lease structure needed"
