# Oil & Gas Lease Compliance Checker - Quick Reference

This guide demonstrates how to use the oil & gas lease compliance checker to analyze counties against the policy: **"All oil & gas leases must be at least 2,500 square miles to qualify for standard terms."**

## 🚀 Quick Start

### Run the Complete Demo

```bash
# Run the demonstration script
python oil_gas_lease_demo.py
```

This will:
1. Query all Texas counties
2. Identify counties below 2,500 sq miles
3. Calculate shortfall for each non-compliant county
4. Rank counties by largest gap first
5. Generate comprehensive compliance reports
6. Save reports to JSON files

### Run Tests

```bash
# Run all tests
pytest tests/test_oil_gas_compliance.py -v

# Or use make
make test
```

## 📊 API Usage

### Basic Usage

```python
from arcgis_client import ArcGISClient
from compliance_checker import analyze_oil_gas_lease_compliance

# ArcGIS Feature Service URL
service_url = (
    "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/"
    "USA_Census_Counties/FeatureServer/0"
)

# Query Texas counties
with ArcGISClient(service_url) as client:
    texas_counties = client.query(where="STATE_NAME = 'Texas'")

# Analyze compliance
report = analyze_oil_gas_lease_compliance(
    texas_counties['features'],
    min_area_sq_miles=2500.0
)

# Access results
print(f"Non-compliant counties: {report['summary']['non_compliant_count']}")
print(f"Compliance rate: {report['summary']['compliance_rate_percentage']}%")

# Top 5 counties with largest shortfall
for county in report['non_compliant_counties'][:5]:
    print(f"{county['county_name']}: {county['shortfall_sq_miles']} sq mi short")
```

### Spatial Query Example

```python
# Find counties within 50 miles of Austin, TX
austin_coords = (-97.7431, 30.2672)

with ArcGISClient(service_url) as client:
    nearby_counties = client.query_nearby(
        point=austin_coords,
        distance_miles=50,
        where="1=1"
    )

# Analyze compliance for nearby counties
report = analyze_oil_gas_lease_compliance(
    nearby_counties['features'],
    min_area_sq_miles=2500.0
)
```

### Include GeoJSON Geometry

```python
# Include geometry for mapping applications
report = analyze_oil_gas_lease_compliance(
    texas_counties['features'],
    min_area_sq_miles=2500.0,
    include_geojson=True  # Includes geometry in results
)

# Each county now has geometry data
for county in report['non_compliant_counties']:
    print(f"{county['county_name']}: {county['geometry']}")
```

## 📋 Report Structure

The `analyze_oil_gas_lease_compliance()` function returns a comprehensive report:

```python
{
    "summary": {
        "total_counties_analyzed": 254,
        "compliant_count": 20,
        "non_compliant_count": 234,
        "invalid_count": 0,
        "compliance_rate_percentage": 7.87,
        "total_shortfall_sq_miles": 458920.45,
        "average_shortfall_sq_miles": 1961.37
    },
    "non_compliant_counties": [
        {
            "county_name": "Loving",
            "state": "Texas",
            "area_sq_miles": 677.0,
            "required_sq_miles": 2500.0,
            "compliant": false,
            "population": 82,
            "shortfall_sq_miles": 1823.0,
            "compliance_percentage": 27.08,
            "recommendation": "Significant consolidation required - consider pooling agreement"
        },
        // ... more counties ranked by shortfall
    ],
    "compliant_counties": [
        // Only included if include_geojson=True
    ],
    "metadata": {
        "policy": "All oil & gas leases must be at least 2,500 acres to qualify for standard terms",
        "minimum_area_requirement_sq_miles": 2500.0,
        "analysis_timestamp": "2025-12-02T10:30:45.123456",
        "include_geometry": false
    }
}
```

## 🎯 Common Use Cases

### 1. Find Top 10 Counties with Largest Shortfall

```python
report = analyze_oil_gas_lease_compliance(features, 2500.0)

print("Top 10 Counties by Shortfall:")
for i, county in enumerate(report['non_compliant_counties'][:10], 1):
    print(f"{i}. {county['county_name']}: {county['shortfall_sq_miles']} sq mi short")
```

### 2. Filter Counties by Compliance Percentage

```python
report = analyze_oil_gas_lease_compliance(features, 2500.0)

# Counties that are close to compliant (>= 90%)
near_compliant = [
    c for c in report['non_compliant_counties']
    if c['compliance_percentage'] >= 90
]

print(f"Counties within 10% of requirement: {len(near_compliant)}")
```

### 3. Generate CSV Export

```python
import csv

report = analyze_oil_gas_lease_compliance(features, 2500.0)

with open('non_compliant_counties.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'county_name', 'state', 'area_sq_miles',
        'shortfall_sq_miles', 'compliance_percentage', 'recommendation'
    ])
    writer.writeheader()
    writer.writerows(report['non_compliant_counties'])
```

### 4. Save Full Report to JSON

```python
import json

report = analyze_oil_gas_lease_compliance(features, 2500.0)

with open('compliance_report.json', 'w') as f:
    json.dump(report, f, indent=2)
```

### 5. Calculate Total Area Needed for Compliance

```python
report = analyze_oil_gas_lease_compliance(features, 2500.0)

total_shortfall = report['summary']['total_shortfall_sq_miles']
print(f"Total additional area needed: {total_shortfall:,.2f} square miles")
```

## 🔍 Understanding Recommendations

The system generates different recommendations based on compliance percentage:

| Compliance % | Recommendation |
|--------------|----------------|
| ≥ 90% | "Consider special terms negotiation - minor shortfall" |
| 75-90% | "Combine with adjacent tracts or apply for non-standard terms" |
| 50-75% | "Significant consolidation required - consider pooling agreement" |
| < 50% | "Does not meet minimum requirements - alternative lease structure needed" |

## 📈 Example Output

```
================================================================================
  Oil & Gas Lease Compliance Analysis - Texas Counties
================================================================================

Querying Texas counties from ArcGIS Feature Service...
✓ Retrieved 254 Texas counties

Analyzing compliance with oil & gas lease policy...
Policy: All leases must be at least 2,500 square miles for standard terms

================================================================================
  Compliance Summary
================================================================================

Total Counties Analyzed:      254
Compliant Counties:           20 (7.87%)
Non-Compliant Counties:       234
Invalid/Missing Data:         0

Total Area Shortfall:         458,920.45 sq mi
Average Shortfall:            1,961.37 sq mi

================================================================================
  Top 10 Non-Compliant Counties (Ranked by Shortfall)
================================================================================

Rank #1: Loving, Texas
  Current Area:         677.00 sq mi
  Required Area:       2500.00 sq mi
  Shortfall:           1823.00 sq mi
  Compliance:            27.08%
  Population:               82
  Recommendation:   Significant consolidation required - consider pooling agreement

Rank #2: King, Texas
  Current Area:         912.00 sq mi
  Required Area:       2500.00 sq mi
  Shortfall:           1588.00 sq mi
  Compliance:            36.48%
  Population:              286
  Recommendation:   Does not meet minimum requirements - alternative lease structure needed

... and more counties
```

## 🧪 Testing

The compliance checker includes comprehensive tests:

```bash
# Run all compliance tests
pytest tests/test_oil_gas_compliance.py -v

# Run specific test
pytest tests/test_oil_gas_compliance.py::TestOilGasLeaseCompliance::test_shortfall_ranking -v

# Run with coverage
pytest tests/test_oil_gas_compliance.py --cov=compliance_checker --cov-report=html
```

## 📚 Additional Resources

- **Full Documentation**: See `README_PRODUCTION.md`
- **API Reference**: Check docstrings in `compliance_checker.py`
- **Examples**: Run `python oil_gas_lease_demo.py`
- **Contributing**: See `CONTRIBUTING.md`

## 🛠️ Troubleshooting

### Issue: No features returned

```python
# Make sure the query is correct
texas_counties = client.query(where="STATE_NAME = 'Texas'")  # Not "Texas'"

# Check feature count
print(f"Retrieved {len(texas_counties['features'])} features")
```

### Issue: Invalid area data

```python
# The analyzer automatically handles invalid data
report = analyze_oil_gas_lease_compliance(features, 2500.0)

# Check for invalid features
if report['summary']['invalid_count'] > 0:
    print(f"Warning: {report['summary']['invalid_count']} features had invalid area data")
```

### Issue: Import errors

```bash
# Make sure you're in the correct directory
cd /path/to/gis-developer-takehome

# Make sure dependencies are installed
pip install -r requirements.txt
```

## 💡 Pro Tips

1. **Use context managers** for automatic resource cleanup:
   ```python
   with ArcGISClient(url) as client:
       data = client.query(where="STATE_NAME = 'Texas'")
   ```

2. **Enable logging** to track analysis progress:
   ```python
   import os
   os.environ['LOG_LEVEL'] = 'INFO'
   ```

3. **Batch processing** for multiple states:
   ```python
   states = ['Texas', 'Oklahoma', 'Louisiana']
   reports = {}

   with ArcGISClient(service_url) as client:
       for state in states:
           data = client.query(where=f"STATE_NAME = '{state}'")
           reports[state] = analyze_oil_gas_lease_compliance(data['features'], 2500.0)
   ```

4. **Custom area requirements**:
   ```python
   # Different requirement for different regions
   report = analyze_oil_gas_lease_compliance(
       features,
       min_area_sq_miles=1500.0  # Custom requirement
   )
   ```

## 📞 Support

For questions or issues:
- Check the logs: `logs/arcgis_client.log`
- Run tests: `make test`
- See examples: `python oil_gas_lease_demo.py`
- Read docs: `README_PRODUCTION.md`
