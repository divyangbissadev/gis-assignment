# Setup and Demos Guide

Complete guide to setting up the project and running all examples and demos.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Configuration](#configuration)
- [Running Examples](#running-examples)
- [Running Demos](#running-demos)
- [Running Tests](#running-tests)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Python 3.9+** (3.12 recommended)
- **pip** (Python package manager)
- **virtualenv** or **venv** (for isolated environments)

### API Keys (Optional)

For NLP Query Parser features, you'll need at least one of:
- **Anthropic API Key** (for Claude models)
- **OpenAI API Key** (for GPT models)
- **Google Gemini API Key** (for Gemini models)

Get your API keys:
- Anthropic: https://console.anthropic.com/
- OpenAI: https://platform.openai.com/api-keys
- Google Gemini: https://ai.google.dev/

---

## Initial Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd gis-assignment
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

**Core Dependencies:**
- `requests` - HTTP client for ArcGIS API
- `anthropic` - Anthropic Claude SDK (for NLP parser)
- `openai` - OpenAI GPT SDK (for NLP parser)
- `google-generativeai` - Google Gemini SDK (for NLP parser)
- `python-dotenv` - Environment variable management

---

## Configuration

### 1. Create Environment File

Create a `.env` file in the project root:

```bash
# Copy the example
cp .env.example .env

# Or create manually
touch .env
```

### 2. Add API Keys

Edit `.env` and add your API keys:

```bash
# Required for NLP Query Parser
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
OPENAI_API_KEY=sk-your-key-here
GEMINI_API_KEY=your-gemini-key-here

# Optional: Logging level
LOG_LEVEL=INFO
```

**Note:** You only need ONE API key to use the NLP query parser. Choose your preferred LLM provider.

### 3. Verify Installation

```bash
# Test basic import
python3 -c "from src.arcgis_client import ArcGISClient; print('✓ Installation successful!')"
```

---

## Running Examples

The `examples/` directory contains production-ready examples for oil & gas compliance.

### Example 1: Basic Texas Compliance Check

```bash
python3 examples/01_basic_texas_compliance.py
```

**What it does:**
- Queries Texas counties from ArcGIS
- Checks oil & gas lease compliance
- Displays results in terminal

**Expected output:**
```
=== Texas Oil & Gas Lease Compliance Analysis ===
Found 254 counties in Texas
✓ Analyzing compliance for 254 leases...
Summary: 240 compliant, 14 non-compliant
```

### Example 2: Spatial Query Near Austin

```bash
python3 examples/02_spatial_query_austin.py
```

**What it does:**
- Finds counties within 50 miles of Austin, TX
- Analyzes compliance for nearby areas
- Shows geographic filtering

### Example 3: Export Results to Files

```bash
python3 examples/03_export_results.py
```

**What it does:**
- Exports results to CSV and JSON formats
- Creates files in `output/` directory
- Demonstrates data export capabilities

**Output files:**
- `output/texas_compliance.csv`
- `output/texas_compliance.json`

### Example 4: Filter and Analyze

```bash
python3 examples/04_filter_and_analyze.py
```

**What it does:**
- Filters results by compliance status
- Analyzes non-compliant leases
- Shows detailed reporting

### Example 5: Batch Multiple States

```bash
python3 examples/05_batch_multiple_states.py
```

**What it does:**
- Analyzes multiple states in batch
- Compares compliance across states
- Generates comparative reports

### Example 6: Custom Thresholds

```bash
python3 examples/06_custom_thresholds.py
```

**What it does:**
- Uses custom compliance thresholds
- Demonstrates configuration flexibility
- Shows warning levels

### Example 7: Session Save/Load

```bash
python3 examples/07_session_save_load.py
```

**What it does:**
- Saves analysis sessions to disk
- Loads previous sessions
- Demonstrates session management

---

## Running Demos

The root directory contains demonstration scripts for new features.

### NLP Query Parser Demo

Demonstrates natural language query parsing with LLM providers.

```bash
python3 nlp_query_demo.py
```

**Features demonstrated:**
- Parse natural language queries
- Convert to ArcGIS WHERE clauses
- Execute queries against live data
- Interactive query mode

**Example queries:**
- "find top 5 counties in Texas under 2500 square miles"
- "counties in California with population over 1 million"
- "show me Harris county in Texas"

**Sample output:**
```
Query: "find top 5 counties in Texas under 2500 square miles"
✓ WHERE Clause: STATE_NAME = 'Texas' AND SQMI < 2500
  ORDER BY: SQMI DESC
  LIMIT: 5
  Confidence: 95.00%

Executing query...
✓ Found 5 features
  Showing 5 of 5 results:
    1. Brewster, Texas - Area: 6193 sq mi, Population: 9,232
    2. Pecos, Texas - Area: 4764 sq mi, Population: 15,507
    ...
```

### Multi-Provider Demo

Demonstrates switching between LLM providers (Anthropic, OpenAI, Gemini).

```bash
python3 multi_provider_demo.py
```

**Features demonstrated:**
- Test all three LLM providers
- Compare results across providers
- Show provider-specific features

### Advanced Query Demo

Demonstrates advanced query features (ORDER BY, LIMIT, aggregations, spatial).

```bash
python3 advanced_query_demo.py
```

**Features demonstrated:**
- Top N queries with ORDER BY
- Aggregation queries (COUNT)
- Spatial proximity queries
- Query caching performance
- Complex multi-filter queries

**Sample output:**
```
Demo 1: Top 5 Largest Counties in California
✓ Query executed successfully
  WHERE: STATE_NAME = 'California'
  ORDER BY: SQMI DESC
  LIMIT: 5

  Results:
    1. San Bernardino County - 20,062 sq mi
    2. Inyo County - 10,181 sq mi
    3. Kern County - 8,161 sq mi
    ...
```

### Cache Demo

Demonstrates ArcGIS query caching with performance metrics.

```bash
python3 cache_demo.py
```

**Features demonstrated:**
- Cache HIT/MISS logging
- Performance improvements (up to 4,780x speedup)
- Cache expiration (TTL)
- Cache management operations
- Performance comparison (with/without caching)

**Sample output:**
```
Demo 1: Basic Caching (Hit/Miss)
Query 1 (First time): STATE_NAME = 'Texas'
Expected: Cache MISS
✓ Completed in 684ms

Query 2 (Same query): STATE_NAME = 'Texas'
Expected: Cache HIT
✓ Completed in 0ms
Speedup: 4780x faster! 🚀

Cache Statistics:
  Total requests: 2
  Cache hits: 1
  Cache misses: 1
  Hit rate: 50.0%
```

### Quick Test Scripts

#### Test Top 5 Query

```bash
python3 test_top_5.py
```

Tests "top N" query functionality with ORDER BY and LIMIT.

#### Test Parser Quick

```bash
python3 test_parser_quick.py
```

Quick test of NLP query parser with a single query.

---

## Running Tests

The `tests/` directory contains unit and integration tests.

### Run All Tests

```bash
# Run entire test suite
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html
```

### Run Specific Test Files

```bash
# Test ArcGIS client
pytest tests/test_arcgis_client.py -v

# Test NLP query parser
pytest tests/test_nlp_query_parser.py -v

# Test compliance checker
pytest tests/test_compliance_checker.py -v

# Test oil & gas compliance
pytest tests/test_oil_gas_compliance.py -v

# Test session manager
pytest tests/test_session_manager.py -v
```

### Test Coverage

```bash
# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html

# Open coverage report
open htmlcov/index.html
```

---

## Troubleshooting

### Common Issues

#### 1. Import Error: No module named 'src'

**Solution:** Make sure you're in the project root directory and the virtual environment is activated.

```bash
# Activate virtual environment
source .venv/bin/activate

# Verify working directory
pwd  # Should show: /path/to/gis-developer-takehome
```

#### 2. API Key Not Found

**Error:** `ArcGISValidationError: ANTHROPIC_API_KEY environment variable not set`

**Solution:** Add your API key to `.env` file:

```bash
echo "ANTHROPIC_API_KEY=your-key-here" >> .env
```

#### 3. API Credit/Quota Exceeded

**Error:** `Your credit balance is too low` or `You exceeded your current quota`

**Solution:**
- Check your API credit balance
- Add credits to your account
- Or switch to a different provider in `.env`

#### 4. Connection Timeout

**Error:** `requests.exceptions.Timeout`

**Solution:**
- Check internet connection
- Verify ArcGIS service is accessible
- Increase timeout in client initialization:

```python
client = ArcGISClient(service_url, timeout=60)
```

#### 5. No Features Found

**Issue:** Query returns 0 features

**Solution:**
- Verify WHERE clause syntax
- Check field names match ArcGIS schema
- Test query in ArcGIS REST API directly

#### 6. Import Error: google.generativeai

**Error:** `ModuleNotFoundError: No module named 'google.generativeai'`

**Solution:**

```bash
pip install google-generativeai
```

### Getting Help

If you encounter issues not covered here:

1. **Check logs**: Review `logs/` directory for detailed error messages
2. **Read documentation**: See [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)
3. **Review examples**: Check example code for usage patterns
4. **Test individually**: Run demos one at a time to isolate issues

---

## Performance Tips

### 1. Enable Caching

For repeated queries, enable caching to improve performance:

```python
client = ArcGISClient(service_url, enable_cache=True, cache_ttl=300)
```

### 2. Use Connection Pooling

The client uses connection pooling by default. For custom sessions:

```python
import requests
session = requests.Session()
session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=10))
client = ArcGISClient(service_url, session=session)
```

### 3. Limit Result Size

For large datasets, use pagination limits:

```python
result = client.query(where="STATE_NAME = 'Texas'", page_size=100, max_pages=5)
```

### 4. Use Spatial Filters

Instead of querying all features and filtering, use spatial queries:

```python
result = client.query_nearby(
    point=(-97.7431, 30.2672),  # Austin, TX
    distance_miles=50,
    where="1=1"
)
```

---

## Next Steps

After setup and testing:

1. **Explore Documentation**: See [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) for module references
2. **Production Deployment**: Review [README_PRODUCTION.md](README_PRODUCTION.md)
3. **Feature Guides**: Check specific guides:
   - [NLP_QUERY_PARSER_README.md](NLP_QUERY_PARSER_README.md) - Natural language queries
   - [MULTI_PROVIDER_SETUP.md](MULTI_PROVIDER_SETUP.md) - LLM provider setup
   - [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md) - Advanced query features
   - [SESSION_GUIDE.md](SESSION_GUIDE.md) - Session management

---

**Last Updated**: 2025-12-02
