# GeoJSON Support Implementation Guide

## ✅ Files with GeoJSON Support (COMPLETED)

1. ✅ **examples/02_spatial_query_austin.py** - Spatial queries near Austin with GeoJSON
2. ✅ **examples/03_export_results.py** - Export compliance results in multiple formats including GeoJSON
3. ✅ **examples/01_basic_state_compliance.py** - Basic state compliance with GeoJSON support

## 📋 Files That Need GeoJSON Support

- `examples/01_basic_texas_compliance.py`
- `examples/02_spatial_query_city.py`
- `examples/04_filter_and_analyze.py`
- `examples/05_batch_multiple_states.py`
- `examples/06_custom_thresholds.py`
- `examples/07_session_save_load.py`

## 🔧 How to Add GeoJSON Support (Step-by-Step)

### Step 1: Add SimpleArcGISClient Import

```python
# Change from:
from src.arcgis_client import ArcGISClient

# To:
from src.arcgis_client import ArcGISClient, SimpleArcGISClient
```

### Step 2: Update Format Choices

```python
# Change from:
parser.add_argument(
    '--format',
    choices=['text', 'json', 'both'],
    default='text',
    help='Output format (default: text)'
)

# To:
parser.add_argument(
    '--format',
    choices=['text', 'json', 'geojson', 'both'],
    default='text',
    help='Output format: text, json, geojson, or both (default: text)'
)
```

### Step 3: Add output_geojson Function

Add this function after `output_json()`:

```python
def output_geojson(report, args, **metadata):
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
            print(f"\n✓ GeoJSON output saved to: {output_file}")
            print(f"  Features: {len(geojson['features'])}")
            print(f"  Compliant: {report['summary']['compliant_count']}")
            print(f"  Non-Compliant: {report['summary']['non_compliant_count']}")
```

### Step 4: Update main() Function

```python
def main():
    args = parse_arguments()

    # Check if GeoJSON format is requested
    needs_geometry = args.format == 'geojson'

    # ... existing setup code ...

    # Query counties - use SimpleArcGISClient for GeoJSON to preserve geometry
    if needs_geometry:
        with SimpleArcGISClient(service_url) as client:
            counties = client.query_features(
                where_clause=f"STATE_NAME = '{state_name}'",
                max_records=1000,
                return_geometry=True,
                paginate=True
            )

            report = analyze_oil_gas_lease_compliance(
                counties['features'],
                min_area_sq_miles=min_area,
                include_geojson=True
            )
    else:
        with ArcGISClient(service_url) as client:
            counties = client.query(
                where=f"STATE_NAME = '{state_name}'",
                page_size=1000
            )

            report = analyze_oil_gas_lease_compliance(
                counties['features'],
                min_area_sq_miles=min_area
            )

    # Output based on format
    if args.format in ['text', 'both'] or (not args.json and not args.output and args.format != 'geojson'):
        print_text_output(report, ...)

    if args.format == 'geojson':
        output_geojson(report, args, state=state_name, min_area_sq_miles=min_area)
    elif args.format in ['json', 'both'] or args.json or args.output:
        output_json(report, ...)
```

### Step 5: Update Documentation

Add GeoJSON examples to the docstring at the top:

```python
"""
Example: Description

Run:
    python examples/filename.py
    python examples/filename.py --format=json
    python examples/filename.py --format=geojson
    python examples/filename.py --format=geojson --output=output.geojson
"""
```

## 🧪 Testing

After adding GeoJSON support, test with:

```bash
# Test GeoJSON output to stdout
python3 examples/filename.py --format=geojson

# Test GeoJSON output to file
python3 examples/filename.py --format=geojson --output=test.geojson --quiet

# Verify the output
python3 -c "
import json
data = json.load(open('test.geojson'))
print('Type:', data['type'])
print('Features:', len(data['features']))
print('Has geometry:', 'geometry' in data['features'][0] if data['features'] else False)
"
```

## 📚 Example Usage

```bash
# Basic state compliance with GeoJSON
python3 examples/01_basic_state_compliance.py --state=California --format=geojson --output=california.geojson

# Spatial query with GeoJSON
python3 examples/02_spatial_query_austin.py --format=geojson --distance=100 --output=austin_100mi.geojson

# Export results in multiple formats including GeoJSON
python3 examples/03_export_results.py --formats=json,csv,geojson --output-dir=results/
```

## 🎯 Key Points

1. **Always use `SimpleArcGISClient`** when GeoJSON is requested to preserve geometry
2. **Set `include_geojson=True`** in `analyze_oil_gas_lease_compliance()` call
3. **Pass metadata** to `output_geojson()` function for context (state, distance, etc.)
4. **Test thoroughly** to ensure geometries are present in output

## 🔍 Common Issues

### Issue: "No geometries available"
**Solution**: Make sure you're using `SimpleArcGISClient` with `return_geometry=True`

### Issue: Geometries are `null`
**Solution**: The `ArcGISClient` wrapper loses geometry. Use `SimpleArcGISClient` directly

### Issue: CSV export fails with geometry field
**Solution**: Filter out geometry fields in CSV export or use `extrasaction='ignore'` in DictWriter

## 📊 File Size Reference

- Small states (e.g., Rhode Island): ~500 KB - 2 MB
- Medium states (e.g., California): ~15 MB - 30 MB
- Large states (e.g., Texas): ~70 MB - 100 MB
- Spatial queries (50 miles): ~3 MB - 10 MB
- Spatial queries (100 miles): ~10 MB - 20 MB

GeoJSON files are larger than regular JSON due to polygon coordinates, but they can be loaded directly into GIS software for visualization.
