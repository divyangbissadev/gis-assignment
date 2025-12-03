"""
Example 2: Spatial Query - Counties Near Austin, TX

This example demonstrates spatial queries to find counties within
50 miles of Austin, TX and check their compliance.

Run:
    python examples/02_spatial_query_austin.py
    python examples/02_spatial_query_austin.py --json
    python examples/02_spatial_query_austin.py --format=json
    python examples/02_spatial_query_austin.py --format=geojson
    python examples/02_spatial_query_austin.py --format=geojson --output=austin_report.geojson
    python examples/02_spatial_query_austin.py --output=austin_report.json
    python examples/02_spatial_query_austin.py --distance=100 --format=geojson
"""

import sys
import os
import json
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.arcgis_client import ArcGISClient, SimpleArcGISClient
from src.compliance_checker import analyze_oil_gas_lease_compliance


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Spatial query: Find counties near Austin, TX and analyze compliance'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON to stdout'
    )
    parser.add_argument(
        '--format',
        choices=['text', 'json', 'geojson', 'both'],
        default='text',
        help='Output format: text, json, geojson, or both (default: text)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Save JSON output to file'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress human-readable output (useful with --output)'
    )
    parser.add_argument(
        '--distance',
        type=int,
        default=50,
        help='Search radius in miles (default: 50)'
    )
    return parser.parse_args()


def print_text_output(report, austin_coords, distance_miles, args):
    """Print human-readable output."""
    if args.quiet:
        return

    print("=" * 80)
    print("AUSTIN AREA COMPLIANCE SUMMARY")
    print("=" * 80)

    summary = report['summary']
    print(f"Counties in Search Area:    {summary['total_counties_analyzed']}")
    print(f"Compliant:                  {summary['compliant_count']}")
    print(f"Non-Compliant:              {summary['non_compliant_count']}")
    print(f"Compliance Rate:            {summary['compliance_rate_percentage']}%")

    # List all counties in the area
    print()
    print("=" * 80)
    print("ALL COUNTIES IN SEARCH AREA")
    print("=" * 80)

    # Combine and sort all counties by area
    all_counties = (
        report['non_compliant_counties'] +
        report['compliant_counties']
    )
    all_counties.sort(key=lambda x: x.get('area_sq_miles', 0), reverse=True)

    for county in all_counties:
        status = "✓ COMPLIANT" if county['compliant'] else "✗ NON-COMPLIANT"
        shortfall = county.get('shortfall_sq_miles', 0)

        print(f"\n{county['county_name']}, {county['state']}")
        print(f"  Area:        {county['area_sq_miles']:>10.2f} sq mi")
        print(f"  Status:      {status}")
        if not county['compliant']:
            print(f"  Shortfall:   {shortfall:>10.2f} sq mi ({county['compliance_percentage']}%)")
            print(f"  Action:      {county['recommendation']}")

    print()
    print("=" * 80)
    print("✓ Analysis Complete!")
    print("=" * 80)


def output_json(report, austin_coords, distance_miles, args):
    """Output JSON data."""
    # Enhance report with query metadata
    enhanced_report = {
        **report,
        'query_metadata': {
            'location': 'Austin, TX',
            'coordinates': {
                'longitude': austin_coords[0],
                'latitude': austin_coords[1]
            },
            'search_radius_miles': distance_miles
        }
    }

    if args.format == 'json' or args.json:
        # Print to stdout
        print(json.dumps(enhanced_report, indent=2))

    if args.output:
        # Save to file
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(enhanced_report, f, indent=2)
        if not args.quiet:
            print(f"\n✓ JSON output saved to: {args.output}")


def output_geojson(report, austin_coords, distance_miles, args):
    """Output GeoJSON data."""
    # Combine all counties
    all_counties = report['non_compliant_counties'] + report['compliant_counties']

    # Filter counties that have geometry
    features_with_geometry = [county for county in all_counties if county.get('geometry')]

    if not features_with_geometry:
        if not args.quiet:
            print("\n⚠ No geometries available for GeoJSON output")
        return

    # Create GeoJSON FeatureCollection
    geojson = {
        "type": "FeatureCollection",
        "metadata": {
            "location": "Austin, TX",
            "coordinates": {
                "longitude": austin_coords[0],
                "latitude": austin_coords[1]
            },
            "search_radius_miles": distance_miles,
            "total_features": len(features_with_geometry),
            "compliant_count": report['summary']['compliant_count'],
            "non_compliant_count": report['summary']['non_compliant_count']
        },
        "features": []
    }

    for county in features_with_geometry:
        feature = {
            "type": "Feature",
            "geometry": county.get('geometry'),
            "properties": {
                "county_name": county.get('county_name'),
                "state": county.get('state'),
                "area_sq_miles": county.get('area_sq_miles'),
                "required_sq_miles": county.get('required_sq_miles'),
                "compliant": county.get('compliant'),
                "population": county.get('population')
            }
        }

        # Add compliance-specific properties
        if county.get('compliant'):
            feature["properties"]["excess_area"] = county.get('excess_area')
        else:
            feature["properties"]["shortfall_sq_miles"] = county.get('shortfall_sq_miles')
            feature["properties"]["compliance_percentage"] = county.get('compliance_percentage')
            feature["properties"]["recommendation"] = county.get('recommendation')

        geojson["features"].append(feature)

    if args.format == 'geojson' and not args.output:
        # Print to stdout only if no output file is specified
        print(json.dumps(geojson, indent=2))

    if args.output:
        # Save to file (use .geojson extension if not specified)
        output_file = args.output
        if args.format == 'geojson' and not output_file.endswith('.geojson'):
            output_file = output_file.rsplit('.', 1)[0] + '.geojson'

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(geojson, f, indent=2)
        if not args.quiet:
            print(f"\n✓ GeoJSON output saved to: {output_file}")
            print(f"  Features: {len(geojson['features'])}")
            print(f"  Compliant: {report['summary']['compliant_count']}")
            print(f"  Non-Compliant: {report['summary']['non_compliant_count']}")


def main():
    args = parse_arguments()

    # Check if GeoJSON format is requested
    needs_geometry = args.format == 'geojson'

    if not args.quiet:
        print("=" * 80)
        print(f"Spatial Query: Counties Within {args.distance} Miles of Austin, TX")
        print("=" * 80)
        print()

    # ArcGIS Feature Service URL
    service_url = os.getenv(
        'ARCGIS_SERVICE_URL',
        "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/"
        "USA_Census_Counties/FeatureServer/0"
    )

    # Austin, TX coordinates (longitude, latitude)
    austin_coords = (-97.7431, 30.2672)
    distance_miles = args.distance

    if not args.quiet:
        print(f"Location: Austin, TX")
        print(f"Coordinates: {austin_coords[1]}°N, {austin_coords[0]}°W")
        print(f"Search Radius: {distance_miles} miles")
        if needs_geometry:
            print("Format: GeoJSON (including geometry)")
        print()

    # Use SimpleArcGISClient for GeoJSON to preserve geometry
    if needs_geometry:
        with SimpleArcGISClient(service_url) as client:
            if not args.quiet:
                print("Executing spatial query with geometry...")

            # Create point geometry for spatial query
            point_geometry = {
                "x": austin_coords[0],
                "y": austin_coords[1],
                "spatialReference": {"wkid": 4326}
            }

            nearby_counties = client.query_features(
                where_clause="1=1",
                return_geometry=True,
                geometry=point_geometry,
                geometry_type="esriGeometryPoint",
                spatial_relationship="esriSpatialRelIntersects",
                distance=distance_miles,
                units="esriSRUnit_StatuteMile",
                paginate=True
            )

            feature_count = len(nearby_counties['features'])
            if not args.quiet:
                print(f"✓ Found {feature_count} counties within {distance_miles} miles of Austin (with geometry)")
                print()
                print("Analyzing compliance...")

            report = analyze_oil_gas_lease_compliance(
                nearby_counties['features'],
                min_area_sq_miles=2500.0,
                include_geojson=True
            )
    else:
        with ArcGISClient(service_url) as client:
            if not args.quiet:
                print("Executing spatial query...")

            nearby_counties = client.query_nearby(
                point=austin_coords,
                distance_miles=distance_miles,
                where="1=1"
            )

            feature_count = len(nearby_counties['features'])
            if not args.quiet:
                print(f"✓ Found {feature_count} counties within {distance_miles} miles of Austin")
                print()
                print("Analyzing compliance...")

            report = analyze_oil_gas_lease_compliance(
                nearby_counties['features'],
                min_area_sq_miles=2500.0
            )

    # Output based on format
    if args.format in ['text', 'both'] or (not args.json and not args.output and args.format != 'geojson'):
        print()
        print_text_output(report, austin_coords, distance_miles, args)

    if args.format == 'geojson' or (args.format == 'both' and needs_geometry):
        output_geojson(report, austin_coords, distance_miles, args)
    elif args.format in ['json', 'both'] or args.json or args.output:
        output_json(report, austin_coords, distance_miles, args)


if __name__ == "__main__":
    main()
