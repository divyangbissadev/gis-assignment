# Runnable Examples - Quick Reference

All examples are ready to run from the project root directory!

## 📁 Examples Directory Structure

```
examples/
├── README.md                          # Detailed examples documentation
├── 01_basic_texas_compliance.py      # ⭐ START HERE - Simplest example
├── 02_spatial_query_austin.py        # Spatial/proximity queries
├── 03_export_results.py              # Export to JSON/CSV/TXT
├── 04_filter_and_analyze.py          # Filter and categorize results
├── 05_batch_multiple_states.py       # Multi-state batch processing
└── 06_custom_thresholds.py           # Policy scenario modeling
```

## 🚀 Quick Run Commands

### ⭐ Example 1: Basic Texas Compliance (Recommended First)
**What it does**: Query Texas counties and show top 5 non-compliant
```bash
python examples/01_basic_texas_compliance.py
```
**Time**: ~10 seconds
**Output**: Console display

---

### 🗺️ Example 2: Spatial Query - Austin Area
**What it does**: Find counties within 50 miles of Austin, TX
```bash
python examples/02_spatial_query_austin.py
```
**Time**: ~8 seconds
**Output**: Console display with all nearby counties

---

### 💾 Example 3: Export Results to Files
**What it does**: Export compliance data to multiple formats
```bash
python examples/03_export_results.py
```
**Time**: ~10 seconds
**Output**: Creates `examples/output/` directory with:
- Full JSON report
- Non-compliant counties CSV
- Compliant counties CSV
- Summary text report

---

### 🔍 Example 4: Filter and Analyze
**What it does**: Categorize counties by compliance levels
```bash
python examples/04_filter_and_analyze.py
```
**Time**: ~10 seconds
**Output**: Console display with filtered categories:
- Near compliant (90-99%)
- Moderately compliant (50-89%)
- Far from compliant (<50%)
- High population counties
- Large shortfall counties

---

### 🌎 Example 5: Batch Multiple States
**What it does**: Analyze 5 states and compare results
```bash
python examples/05_batch_multiple_states.py
```
**Time**: ~45-60 seconds (queries 5 states)
**Output**:
- State comparison table
- Top 10 worst counties across all states
- Overall statistics

**Note**: This example takes longer as it processes multiple states

---

### ⚙️ Example 6: Custom Thresholds
**What it does**: Model different policy scenarios
```bash
python examples/06_custom_thresholds.py
```
**Time**: ~30 seconds (tests 6 thresholds)
**Output**:
- Comparison of 6 different thresholds
- Impact analysis
- Policy recommendations

---

## 📊 Sample Output Preview

### Example 1 - Basic Output
```
================================================================================
TOP 5 NON-COMPLIANT COUNTIES (Ranked by Shortfall)
================================================================================

1. Rockwall County
   Current Area:        148.93 sq mi
   Shortfall:          2351.07 sq mi
   Compliance:            5.96%
   Recommendation:  Does not meet minimum requirements

2. Somervell County
   Current Area:        191.69 sq mi
   Shortfall:          2308.31 sq mi
   Compliance:            7.67%
   Recommendation:  Does not meet minimum requirements

... and 240 more non-compliant counties
```

### Example 3 - File Exports
```
examples/output/
├── full_report_20251202_103045.json              # Complete analysis
├── non_compliant_counties_20251202_103045.csv    # 245 non-compliant
├── compliant_counties_20251202_103045.csv        # 9 compliant
└── summary_report_20251202_103045.txt            # Human-readable
```

### Example 5 - Multi-State Comparison
```
STATE COMPARISON TABLE
State           Total    Compliant    Non-Comp     Rate %
Louisiana       64       5            59           7.81
New Mexico      33       7            26           21.21
Oklahoma        77       1            76           1.30
Texas           254      9            245          3.54
Wyoming         23       7            16           30.43
```

## 🎯 Recommended Learning Path

1. **Start Here** → Example 1 (Basic)
   - Understand the basics
   - See simple query and analysis

2. **Next** → Example 2 (Spatial Query)
   - Learn spatial queries
   - Proximity-based analysis

3. **Then** → Example 3 (Export)
   - Save results to files
   - Work with data in Excel/other tools

4. **Advanced** → Example 4 (Filtering)
   - Filter and categorize
   - Targeted analysis

5. **Batch** → Example 5 (Multi-State)
   - Process multiple states
   - Comparative analysis

6. **Modeling** → Example 6 (Scenarios)
   - Test policy changes
   - What-if analysis

## 🔧 Customization Examples

### Change the Area Threshold
```python
# In any example, modify this line:
report = analyze_oil_gas_lease_compliance(
    features,
    min_area_sq_miles=1500.0  # Change from 2500 to 1500
)
```

### Query a Different State
```python
# Change Texas to Oklahoma:
counties = client.query(where="STATE_NAME = 'Oklahoma'")
```

### Change Search Location (Example 2)
```python
# Change from Austin to Houston:
houston_coords = (-95.3698, 29.7604)
nearby = client.query_nearby(
    point=houston_coords,
    distance_miles=100  # Also increase distance
)
```

### Export to Different Directory
```python
# In Example 3:
output_dir = "my_reports"  # Instead of "examples/output"
```

## ✅ Verification

All examples have been tested and work correctly:
- ✅ Example 1: Basic Texas Compliance
- ✅ Example 2: Spatial Query Austin
- ✅ Example 3: Export Results
- ✅ Example 4: Filter and Analyze
- ✅ Example 5: Batch Multiple States
- ✅ Example 6: Custom Thresholds

## 📋 Requirements

All examples require:
- Python 3.8+
- Internet connection (to query ArcGIS services)
- Dependencies installed: `pip install -r requirements.txt`

## 🐛 Troubleshooting

### "Module not found" Error
```bash
# Run from project root:
cd /path/to/gis-developer-takehome
python examples/01_basic_texas_compliance.py
```

### Network Timeout
```bash
# Examples need internet to query ArcGIS
# Check your connection and try again
```

### Slow Performance
- Example 1-4: Fast (~10 seconds each)
- Example 5: Slower (~60 seconds - queries 5 states)
- Example 6: Moderate (~30 seconds - 6 thresholds)

## 📚 Documentation

- **Detailed Examples Guide**: `examples/README.md`
- **API Documentation**: `OIL_GAS_LEASE_GUIDE.md`
- **Full Demo Script**: `oil_gas_lease_demo.py`
- **Test Suite**: `tests/test_oil_gas_compliance.py`

## 🎓 Next Steps

After running examples:
1. Review the code in each example file
2. Modify parameters to test different scenarios
3. Check the output files (Example 3)
4. Read `OIL_GAS_LEASE_GUIDE.md` for API details
5. Create your own custom analysis scripts

## 💡 Pro Tips

1. **Start with Example 1** - It's the simplest
2. **Use Example 3** - To save results for Excel analysis
3. **Try Example 6** - To model "what-if" scenarios
4. **Check the logs** - Structured logs in `logs/` directory
5. **Modify and experiment** - All examples are well-commented

---

**Ready to run? Start with:**
```bash
python examples/01_basic_texas_compliance.py
```
