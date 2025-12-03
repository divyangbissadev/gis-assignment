#!/usr/bin/env python3
"""
Helper script to add GeoJSON support to example files.
This adds the necessary imports, format options, and output functions.
"""

import sys
import re

# GeoJSON output function template
GEOJSON_FUNCTION = '''

def output_geojson(report, args, **metadata):
    """Output GeoJSON data."""
    # Combine all counties
    all_counties = report['non_compliant_counties'] + report['compliant_counties']

    # Filter counties that have geometry
    features_with_geometry = [county for county in all_counties if county.get('geometry')]

    if not features_with_geometry:
        if not args.quiet:
            print("\\n⚠ No geometries available for GeoJSON output")
        return

    # Create GeoJSON FeatureCollection
    geojson = {
        "type": "FeatureCollection",
        "metadata": {
            **metadata,
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
            print(f"\\n✓ GeoJSON output saved to: {output_file}")
            print(f"  Features: {len(geojson['features'])}")
            print(f"  Compliant: {report['summary']['compliant_count']}")
            print(f"  Non-Compliant: {report['summary']['non_compliant_count']}")
'''

def add_simple_arcgis_import(content):
    """Add SimpleArcGISClient to imports if not present."""
    if 'SimpleArcGISClient' in content:
        return content

    # Find ArcGISClient import and add SimpleArcGISClient
    pattern = r'from src\.arcgis_client import ArcGISClient\b(?!, SimpleArcGISClient)'
    replacement = 'from src.arcgis_client import ArcGISClient, SimpleArcGISClient'
    content = re.sub(pattern, replacement, content)

    return content

def add_geojson_to_format_choices(content):
    """Add 'geojson' to format choices if not present."""
    if "'geojson'" in content or '"geojson"' in content:
        return content

    # Find choices parameter and add geojson
    pattern = r"choices=\['text', 'json', 'both'\]"
    replacement = "choices=['text', 'json', 'geojson', 'both']"
    content = re.sub(pattern, replacement, content)

    # Update help text
    pattern = r"help='Output format \(default: text\)'"
    replacement = "help='Output format: text, json, geojson, or both (default: text)'"
    content = re.sub(pattern, replacement, content)

    return content

def add_geojson_function(content):
    """Add the output_geojson function if not present."""
    if 'def output_geojson' in content:
        return content

    # Find the location after output_json function
    pattern = r'(def output_json\([^)]+\):.*?(?=\n\ndef|\n\nif __name__|\Z))'
    match = re.search(pattern, content, re.DOTALL)

    if match:
        insert_pos = match.end()
        content = content[:insert_pos] + GEOJSON_FUNCTION + content[insert_pos:]

    return content

def process_file(filepath):
    """Process a single file to add GeoJSON support."""
    print(f"Processing {filepath}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Apply transformations
    content = add_simple_arcgis_import(content)
    content = add_geojson_to_format_choices(content)
    content = add_geojson_function(content)

    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ Updated {filepath}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 add_geojson_support.py <file1> <file2> ...")
        sys.exit(1)

    for filepath in sys.argv[1:]:
        try:
            process_file(filepath)
        except Exception as e:
            print(f"✗ Error processing {filepath}: {e}")
