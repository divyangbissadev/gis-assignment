"""
Oil & Gas Lease Compliance Demonstration

This script demonstrates the analysis of counties for oil & gas lease
compliance based on a configurable policy (default: "All oil & gas leases
must be at least 2,500 square miles to qualify for standard terms.")

Requirements demonstrated:
1. Query state counties from ArcGIS Feature Service
2. Query counties within specified radius of a city
3. Identify counties BELOW minimum area threshold
4. Calculate shortfall for each non-compliant county
5. Rank counties by largest gap first
6. Generate comprehensive compliance report

Run:
    python examples/14_oil_gas_lease_demo.py
    python examples/14_oil_gas_lease_demo.py --state=California
    python examples/14_oil_gas_lease_demo.py --state=Texas --min-area=3000.0
    python examples/14_oil_gas_lease_demo.py --state=Texas --city=Austin --radius=100
"""

import sys
import os
import json
import argparse
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.arcgis_client import ArcGISClient
from src.compliance_checker import analyze_oil_gas_lease_compliance
from src.errors import ArcGISError, ComplianceError
from src.logger import get_logger

logger = get_logger(__name__)


# Known city coordinates for spatial queries
CITY_COORDINATES = {
    'Austin': (-97.7431, 30.2672),
    'Houston': (-95.3698, 29.7604),
    'Dallas': (-96.7970, 32.7767),
    'San Antonio': (-98.4936, 29.4241),
    'Los Angeles': (-118.2437, 34.0522),
    'San Francisco': (-122.4194, 37.7749),
    'Sacramento': (-121.4944, 38.5816),
    'Denver': (-104.9903, 39.7392),
    'Oklahoma City': (-97.5164, 35.4676),
    'Tulsa': (-95.9928, 36.1540),
}


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Oil & Gas Lease Compliance Demonstration'
    )
    parser.add_argument(
        '--state',
        type=str,
        default='Texas',
        help='State to analyze (default: Texas)'
    )
    parser.add_argument(
        '--min-area',
        type=float,
        default=2500.0,
        help='Minimum area requirement in square miles (default: 2500.0)'
    )
    parser.add_argument(
        '--city',
        type=str,
        help='City name for spatial query (e.g., Austin, Houston, Dallas)'
    )
    parser.add_argument(
        '--city-coords',
        type=str,
        help='Custom city coordinates as "longitude,latitude" (e.g., "-97.7431,30.2672")'
    )
    parser.add_argument(
        '--radius',
        type=float,
        default=50.0,
        help='Radius in miles for spatial query (default: 50.0)'
    )
    parser.add_argument(
        '--skip-spatial',
        action='store_true',
        help='Skip spatial query demonstration'
    )
    return parser.parse_args()


def print_section_header(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_county_details(county: Dict[str, Any], rank: int) -> None:
    """Print formatted county compliance details."""
    print(f"\nRank #{rank}: {county['county_name']}, {county['state']}")
    print(f"  Current Area:     {county['area_sq_miles']:>10.2f} sq mi")
    print(f"  Required Area:    {county['required_sq_miles']:>10.2f} sq mi")
    print(f"  Shortfall:        {county['shortfall_sq_miles']:>10.2f} sq mi")
    print(f"  Compliance:       {county['compliance_percentage']:>10.2f}%")
    print(f"  Population:       {county['population']:>10,}")
    print(f"  Recommendation:   {county['recommendation']}")


def save_report_to_file(report: Dict[str, Any], filename: str) -> None:
    """Save compliance report to JSON file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Report saved to {filename}")
        print(f"\n✓ Full report saved to: {filename}")
    except Exception as e:
        logger.error(f"Failed to save report: {e}")
        print(f"\n✗ Failed to save report: {e}")


def demonstrate_state_counties_analysis(state: str, min_area: float) -> int:
    """
    Demonstrate oil & gas lease compliance analysis for all state counties.

    Args:
        state: State name to analyze.
        min_area: Minimum area requirement in square miles.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    print_section_header(f"Oil & Gas Lease Compliance Analysis - {state} Counties")

    # ArcGIS Service URL for USA Counties
    service_url = os.getenv(
        'ARCGIS_SERVICE_URL',
        "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/"
        "USA_Census_Counties/FeatureServer/0"
    )

    logger.info(f"Starting {state} counties analysis")

    try:
        # Initialize ArcGIS client with context manager for automatic cleanup
        with ArcGISClient(service_url) as client:
            print(f"Querying {state} counties from ArcGIS Feature Service...")
            print(f"Service URL: {service_url}")

            # Query all state counties
            state_counties = client.query(
                where=f"STATE_NAME = '{state}'",
                page_size=500,
                paginate=True
            )

            feature_count = len(state_counties.get('features', []))
            print(f"✓ Retrieved {feature_count} {state} counties\n")

            # Analyze compliance
            print("Analyzing compliance with oil & gas lease policy...")
            print(f"Policy: All leases must be at least {min_area} square miles for standard terms")

            report = analyze_oil_gas_lease_compliance(
                state_counties['features'],
                min_area_sq_miles=min_area,
                include_geojson=False
            )

            # Display summary
            print_section_header("Compliance Summary")
            summary = report['summary']
            print(f"Total Counties Analyzed:      {summary['total_counties_analyzed']}")
            print(f"Compliant Counties:           {summary['compliant_count']} ({summary['compliance_rate_percentage']}%)")
            print(f"Non-Compliant Counties:       {summary['non_compliant_count']}")
            print(f"Invalid/Missing Data:         {summary['invalid_count']}")
            print(f"\nTotal Area Shortfall:         {summary['total_shortfall_sq_miles']:,.2f} sq mi")
            print(f"Average Shortfall:            {summary['average_shortfall_sq_miles']:,.2f} sq mi")

            # Display top 10 non-compliant counties by shortfall
            print_section_header("Top 10 Non-Compliant Counties (Ranked by Shortfall)")
            non_compliant = report['non_compliant_counties']

            if non_compliant:
                for i, county in enumerate(non_compliant[:10], 1):
                    print_county_details(county, i)

                # Show total count if more than 10
                if len(non_compliant) > 10:
                    print(f"\n... and {len(non_compliant) - 10} more non-compliant counties")
            else:
                print("✓ All counties meet the minimum area requirement!")

            # Save full report
            filename = f"{state.lower().replace(' ', '_')}_counties_compliance_report.json"
            save_report_to_file(report, filename)

            logger.info(f"{state} counties analysis completed successfully")
            return 0

    except ArcGISError as e:
        logger.error(f"ArcGIS query failed: {e}", exc_info=True)
        print(f"\n✗ Error querying ArcGIS service: {e}")
        return 1

    except ComplianceError as e:
        logger.error(f"Compliance analysis failed: {e}", exc_info=True)
        print(f"\n✗ Error analyzing compliance: {e}")
        return 1

    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        print(f"\n✗ Unexpected error: {e}")
        return 1


def demonstrate_city_spatial_query(city_name: str, city_coords: tuple, radius: float, min_area: float) -> int:
    """
    Demonstrate spatial query for counties within specified radius of a city.

    Args:
        city_name: Name of the city.
        city_coords: Tuple of (longitude, latitude).
        radius: Radius in miles for the spatial query.
        min_area: Minimum area requirement in square miles.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    print_section_header(f"Spatial Query - Counties Within {radius} Miles of {city_name}")

    service_url = os.getenv(
        'ARCGIS_SERVICE_URL',
        "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/"
        "USA_Census_Counties/FeatureServer/0"
    )

    logger.info(f"Starting {city_name} spatial query")

    try:
        with ArcGISClient(service_url) as client:
            print(f"Querying counties within {radius} miles of {city_name}")
            print(f"{city_name} coordinates: {city_coords[1]}, {city_coords[0]}")

            # Spatial query
            nearby_counties = client.query_nearby(
                point=city_coords,
                distance_miles=radius,
                where="1=1",
                page_size=500
            )

            feature_count = len(nearby_counties.get('features', []))
            print(f"✓ Retrieved {feature_count} counties near {city_name}\n")

            # Analyze compliance
            print(f"Analyzing compliance for counties near {city_name}...")

            report = analyze_oil_gas_lease_compliance(
                nearby_counties['features'],
                min_area_sq_miles=min_area,
                include_geojson=False
            )

            # Display summary
            print_section_header(f"{city_name} Area Compliance Summary")
            summary = report['summary']
            print(f"Counties Within {radius} Miles:  {summary['total_counties_analyzed']}")
            print(f"Compliant:                    {summary['compliant_count']}")
            print(f"Non-Compliant:                {summary['non_compliant_count']}")
            print(f"Compliance Rate:              {summary['compliance_rate_percentage']}%")

            # Display all non-compliant counties in the area
            print_section_header(f"Non-Compliant Counties Near {city_name}")
            non_compliant = report['non_compliant_counties']

            if non_compliant:
                for i, county in enumerate(non_compliant, 1):
                    print_county_details(county, i)
            else:
                print(f"✓ All counties near {city_name} meet the minimum area requirement!")

            # Save report
            filename = f"{city_name.lower().replace(' ', '_')}_area_compliance_report.json"
            save_report_to_file(report, filename)

            logger.info(f"{city_name} spatial query completed successfully")
            return 0

    except ArcGISError as e:
        logger.error(f"Spatial query failed: {e}", exc_info=True)
        print(f"\n✗ Error executing spatial query: {e}")
        return 1

    except ComplianceError as e:
        logger.error(f"Compliance analysis failed: {e}", exc_info=True)
        print(f"\n✗ Error analyzing compliance: {e}")
        return 1

    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        print(f"\n✗ Unexpected error: {e}")
        return 1


def demonstrate_api_usage(state: str, min_area: float) -> None:
    """Demonstrate basic API usage with code examples."""
    print_section_header("API Usage Examples")

    example_code = f'''
# Example 1: Basic compliance analysis
from src.arcgis_client import ArcGISClient
from src.compliance_checker import analyze_oil_gas_lease_compliance

service_url = "https://services.arcgis.com/.../FeatureServer/0"

# Query {state} counties
with ArcGISClient(service_url) as client:
    state_data = client.query(where="STATE_NAME = '{state}'")

# Analyze compliance
report = analyze_oil_gas_lease_compliance(
    state_data['features'],
    min_area_sq_miles={min_area}
)

# Access results
print(f"Non-compliant: {{report['summary']['non_compliant_count']}}")
for county in report['non_compliant_counties'][:5]:
    print(f"{{county['county_name']}}: {{county['shortfall_sq_miles']}} sq mi short")

# Example 2: Spatial query near a location
city_coords = (-97.7431, 30.2672)  # Example: Austin, TX
nearby = client.query_nearby(
    point=city_coords,
    distance_miles=50
)

# Analyze nearby counties
report = analyze_oil_gas_lease_compliance(nearby['features'], min_area_sq_miles={min_area})

# Example 3: Include GeoJSON geometry in results
report = analyze_oil_gas_lease_compliance(
    state_data['features'],
    min_area_sq_miles={min_area},
    include_geojson=True  # Includes geometry for mapping
)

# Example 4: Access specific report sections
summary = report['summary']
non_compliant = report['non_compliant_counties']
metadata = report['metadata']

# Save to file
import json
with open('compliance_report.json', 'w') as f:
    json.dump(report, f, indent=2)
'''

    print(example_code)


def main() -> int:
    """
    Main entry point for oil & gas lease compliance demonstration.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    args = parse_arguments()

    logger.info("Oil & Gas Lease Compliance Demo starting")

    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  Oil & Gas Lease Compliance Analysis - Demonstration".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("║" + f"  State: {args.state}".center(78) + "║")
    print("║" + f"  Minimum Area: {args.min_area} square miles".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "═" * 78 + "╝")

    # Run demonstrations
    try:
        # 1. Analyze all state counties
        result = demonstrate_state_counties_analysis(args.state, args.min_area)
        if result != 0:
            return result

        # 2. Spatial query near city (if specified)
        if not args.skip_spatial:
            # Determine city coordinates
            if args.city_coords:
                try:
                    lon, lat = map(float, args.city_coords.split(','))
                    city_coords = (lon, lat)
                    city_name = args.city or "Custom Location"
                except ValueError:
                    print("\n✗ Invalid city coordinates format. Use 'longitude,latitude'")
                    return 1
            elif args.city:
                city_name = args.city
                if city_name in CITY_COORDINATES:
                    city_coords = CITY_COORDINATES[city_name]
                else:
                    print(f"\n✗ Unknown city: {city_name}")
                    print(f"Available cities: {', '.join(CITY_COORDINATES.keys())}")
                    print("Or use --city-coords to specify custom coordinates")
                    return 1
            else:
                # Default to Austin for Texas, or skip for other states
                if args.state == 'Texas':
                    city_name = 'Austin'
                    city_coords = CITY_COORDINATES['Austin']
                else:
                    # Skip spatial query for non-Texas states by default
                    city_name = None
                    city_coords = None

            if city_coords:
                result = demonstrate_city_spatial_query(city_name, city_coords, args.radius, args.min_area)
                if result != 0:
                    return result

        # 3. Show API usage examples
        demonstrate_api_usage(args.state, args.min_area)

        print_section_header("Demonstration Complete")
        print("✓ All analyses completed successfully")
        print("\nGenerated Reports:")
        state_filename = f"{args.state.lower().replace(' ', '_')}_counties_compliance_report.json"
        print(f"  - {state_filename}")
        if not args.skip_spatial and (args.city or args.city_coords or args.state == 'Texas'):
            city_name = args.city or (args.city_coords and "Custom Location") or "Austin"
            city_filename = f"{city_name.lower().replace(' ', '_')}_area_compliance_report.json"
            print(f"  - {city_filename}")
        print("\nCheck the logs/ directory for detailed execution logs.")

        logger.info("Demo completed successfully")
        return 0

    except KeyboardInterrupt:
        print("\n\n✗ Demo interrupted by user")
        logger.warning("Demo interrupted by user")
        return 130

    except Exception as e:
        print(f"\n✗ Demo failed: {e}")
        logger.critical(f"Demo failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
