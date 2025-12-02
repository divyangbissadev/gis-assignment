# Documentation Index

Complete index of all documentation and module references for the GIS Developer ArcGIS Client project.

## Table of Contents

- [Quick Start](#quick-start)
- [Core Documentation](#core-documentation)
- [Module Documentation](#module-documentation)
- [Feature Guides](#feature-guides)
- [API Reference](#api-reference)
- [Examples & Demos](#examples--demos)
- [Development](#development)
- [Deployment](#deployment)

---

## Quick Start

### New Users - Start Here

| Order | Document | Description |
|-------|----------|-------------|
| 1 | [../README.md](../README.md) | Project overview and quick introduction |
| 2 | [SETUP_AND_DEMOS.md](SETUP_AND_DEMOS.md) | **Complete setup guide and running all demos** |
| 3 | [EXAMPLES_SUMMARY.md](EXAMPLES_SUMMARY.md) | Quick reference for all examples |

### Developers - Start Here

| Order | Document | Description |
|-------|----------|-------------|
| 1 | [SETUP_AND_DEMOS.md](SETUP_AND_DEMOS.md) | Setup and test environment |
| 2 | [STRUCTURE.md](STRUCTURE.md) | Project structure and architecture |
| 3 | [CONTRIBUTING.md](CONTRIBUTING.md) | Development guidelines |

### Production Deployment

| Order | Document | Description |
|-------|----------|-------------|
| 1 | [README_PRODUCTION.md](README_PRODUCTION.md) | Production deployment guide |
| 2 | [PRODUCTION_UPGRADE.md](PRODUCTION_UPGRADE.md) | Recent upgrades and changes |
| 3 | [SETUP_AND_DEMOS.md](SETUP_AND_DEMOS.md) | Verify setup with demos |

---

## Core Documentation

### Main Documentation

| Document | Location | Description |
|----------|----------|-------------|
| **Project README** | [../README.md](../README.md) | Main project overview, features, and quick start |
| **Setup & Demos** | [SETUP_AND_DEMOS.md](SETUP_AND_DEMOS.md) | Complete setup guide with all examples and demos |
| **Documentation Index** | [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) | This file - central index of all docs |
| **Project Structure** | [STRUCTURE.md](STRUCTURE.md) | Directory structure and code organization |

---

## Module Documentation

Detailed documentation for each Python module in the `src/` directory.

### Core Modules

#### 1. ArcGIS Client (`src/arcgis_client.py`)

**Purpose:** Core client for querying ArcGIS Feature Services

**Documentation:**
- [README_PRODUCTION.md - ArcGIS Client](README_PRODUCTION.md#arcgis-client) - Production API reference
- [PAGINATION_ANALYSIS.md](PAGINATION_ANALYSIS.md) - Pagination implementation
- [SETUP_AND_DEMOS.md - Cache Demo](SETUP_AND_DEMOS.md#cache-demo) - Caching features

**Key Features:**
- Query features with WHERE clauses
- Spatial queries (nearby, within distance)
- Automatic pagination for large datasets
- Query result caching with TTL
- Connection pooling and retry logic
- Comprehensive error handling

**API Reference:**

```python
from src.arcgis_client import ArcGISClient

# Initialize
client = ArcGISClient(
    service_url="https://...",
    enable_cache=True,      # Enable query caching
    cache_ttl=300,          # Cache TTL in seconds
    timeout=30              # Request timeout
)

# Basic query
result = client.query(
    where="STATE_NAME = 'Texas'",
    page_size=1000,
    max_pages=None
)

# Spatial query
result = client.query_nearby(
    point=(-97.7431, 30.2672),  # (lon, lat)
    distance_miles=50,
    where="1=1"
)

# Cache management
stats = client.get_cache_stats()
client.clear_cache()
```

**Related Files:**
- Source: `src/arcgis_client.py`
- Tests: `tests/test_arcgis_client.py`
- Demos: `cache_demo.py`

---

#### 2. NLP Query Parser (`src/nlp_query_parser.py`)

**Purpose:** Parse natural language queries into ArcGIS WHERE clauses using LLMs

**Documentation:**
- [NLP_QUERY_PARSER_README.md](NLP_QUERY_PARSER_README.md) - Complete NLP parser guide
- [MULTI_PROVIDER_SETUP.md](MULTI_PROVIDER_SETUP.md) - LLM provider setup
- [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md) - Advanced query features

**Key Features:**
- Natural language to SQL WHERE clause conversion
- Support for ORDER BY, LIMIT, aggregations
- Spatial filter parsing
- Query result caching (separate from ArcGIS cache)
- Multi-provider support (Anthropic, OpenAI, Gemini)
- Confidence scoring and explanations

**API Reference:**

```python
from src.nlp_query_parser import NLPQueryParser

# Initialize with provider
parser = NLPQueryParser(
    provider='anthropic',  # 'anthropic', 'openai', or 'gemini'
    api_key=None,          # Uses env var if not provided
    enable_cache=True,     # Cache parsed queries
    cache_ttl=3600         # 1 hour default
)

# Parse query
result = parser.parse("find top 5 counties in Texas under 2500 square miles")

# Access parsed components
print(result.where_clause)    # "STATE_NAME = 'Texas' AND SQMI < 2500"
print(result.order_by)        # "SQMI DESC"
print(result.limit)           # 5
print(result.confidence)      # 0.95
print(result.explanation)     # Detailed explanation

# Get supported queries
examples = NLPQueryParser.get_supported_queries()

# Get field mappings
mappings = NLPQueryParser.get_field_mappings()
```

**Related Files:**
- Source: `src/nlp_query_parser.py`
- Tests: `tests/test_nlp_query_parser.py`
- Demos: `nlp_query_demo.py`, `multi_provider_demo.py`

---

#### 3. LLM Providers (`src/llm_providers.py`)

**Purpose:** Abstraction layer for multiple LLM providers

**Documentation:**
- [MULTI_PROVIDER_SETUP.md](MULTI_PROVIDER_SETUP.md) - Provider configuration guide

**Key Features:**
- Unified interface for Anthropic Claude, OpenAI GPT, Google Gemini
- Automatic API key management from environment
- Model selection per provider
- Error handling and validation

**API Reference:**

```python
from src.llm_providers import create_provider, AnthropicProvider, OpenAIProvider, GeminiProvider

# Create provider (factory)
provider = create_provider(
    provider='anthropic',     # 'anthropic', 'openai', or 'gemini'
    api_key=None,             # Optional, uses env var
    model=None                # Optional, uses default
)

# Generate text
response = provider.generate(
    prompt="Your prompt here",
    max_tokens=1024
)

# Direct provider creation
anthropic = AnthropicProvider(model='claude-sonnet-4-5-20250929')
openai = OpenAIProvider(model='gpt-4o')
gemini = GeminiProvider(model='gemini-2.0-flash')
```

**Supported Models:**
- Anthropic: `claude-sonnet-4-5-20250929`, `claude-3-5-sonnet-20241022`
- OpenAI: `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo`
- Gemini: `gemini-2.0-flash`, `gemini-1.5-pro`

**Related Files:**
- Source: `src/llm_providers.py`
- Demos: `multi_provider_demo.py`

---

#### 4. Query Executor (`src/query_executor.py`)

**Purpose:** Execute advanced queries with ORDER BY, LIMIT, aggregations, spatial filters

**Documentation:**
- [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md) - Complete advanced features guide

**Key Features:**
- ORDER BY implementation (client-side sorting)
- LIMIT implementation (result limiting)
- Aggregation support (COUNT, SUM, AVG)
- Spatial query execution
- Automatic pagination for sorted queries

**API Reference:**

```python
from src.query_executor import execute_query, QueryExecutor
from src.nlp_query_parser import ParsedQuery

# Using convenience function
result = execute_query(
    client=arcgis_client,
    parsed_query=parsed_query,
    max_results=1000
)

# Using QueryExecutor class
executor = QueryExecutor(arcgis_client)
result = executor.execute(parsed_query, max_results=1000)

# Result structure
{
    "type": "FeatureCollection",
    "features": [...],
    "count": 5,
    "query": {
        "where_clause": "...",
        "order_by": "SQMI DESC",
        "limit": 5
    },
    "explanation": "...",
    "confidence": 0.95
}
```

**Related Files:**
- Source: `src/query_executor.py`
- Demos: `advanced_query_demo.py`, `test_top_5.py`

---

#### 5. Compliance Checker (`src/compliance_checker.py`)

**Purpose:** Check oil & gas lease compliance against regulations

**Documentation:**
- [OIL_GAS_LEASE_GUIDE.md](OIL_GAS_LEASE_GUIDE.md) - Complete compliance guide

**Key Features:**
- Configurable compliance rules and thresholds
- Multi-criteria compliance checking
- Detailed violation reporting
- Batch compliance analysis

**API Reference:**

```python
from src.compliance_checker import ComplianceChecker, ComplianceRules

# Create custom rules
rules = ComplianceRules(
    max_area_sqmi=2500,
    max_perimeter_mi=200,
    min_population=1000,
    max_population=1000000
)

# Initialize checker
checker = ComplianceChecker(rules)

# Check single lease
result = checker.check_compliance(lease_data)

# Batch check
results = checker.check_batch(leases)

# Result structure
{
    "compliant": True/False,
    "lease_id": "...",
    "violations": [...],
    "warnings": [...],
    "details": {...}
}
```

**Related Files:**
- Source: `src/compliance_checker.py`
- Tests: `tests/test_compliance_checker.py`, `tests/test_oil_gas_compliance.py`
- Examples: `examples/01_basic_texas_compliance.py`

---

#### 6. Session Manager (`src/session_manager.py`)

**Purpose:** Save and load analysis sessions to/from disk

**Documentation:**
- [SESSION_GUIDE.md](SESSION_GUIDE.md) - Session management guide

**Key Features:**
- Save/load analysis sessions as JSON
- Preserve query parameters and results
- Session metadata tracking
- Compression support for large sessions

**API Reference:**

```python
from src.session_manager import SessionManager

# Initialize
manager = SessionManager(save_dir="sessions/")

# Save session
session_id = manager.save_session(
    query_params={"where": "STATE_NAME = 'Texas'"},
    results=features,
    metadata={"user": "analyst"}
)

# Load session
session = manager.load_session(session_id)

# List sessions
sessions = manager.list_sessions()

# Delete session
manager.delete_session(session_id)
```

**Related Files:**
- Source: `src/session_manager.py`
- Tests: `tests/test_session_manager.py`
- Examples: `examples/07_session_save_load.py`

---

#### 7. Logger (`src/logger.py`)

**Purpose:** Centralized JSON logging with structured output

**Key Features:**
- JSON-formatted logs
- Multiple log levels (DEBUG, INFO, WARNING, ERROR)
- File and console handlers
- Automatic log rotation

**API Reference:**

```python
from src.logger import get_logger

# Get logger for module
logger = get_logger(__name__)

# Log messages
logger.info("Message", extra={"key": "value"})
logger.warning("Warning message")
logger.error("Error message", exc_info=True)
```

**Related Files:**
- Source: `src/logger.py`
- Log output: `logs/` directory

---

#### 8. Errors (`src/errors.py`)

**Purpose:** Custom exception classes for error handling

**Exception Hierarchy:**

```python
from src.errors import (
    ArcGISError,              # Base exception
    ArcGISConnectionError,    # Network/connection errors
    ArcGISValidationError,    # Validation errors
    ArcGISQueryError          # Query execution errors
)

# Usage
try:
    result = client.query(where="...")
except ArcGISQueryError as e:
    print(f"Query failed: {e}")
except ArcGISConnectionError as e:
    print(f"Connection failed: {e}")
```

**Related Files:**
- Source: `src/errors.py`

---

## Feature Guides

Comprehensive guides for specific features and use cases.

| Guide | File | Topics Covered |
|-------|------|----------------|
| **NLP Query Parser** | [NLP_QUERY_PARSER_README.md](NLP_QUERY_PARSER_README.md) | Natural language parsing, supported queries, examples |
| **Multi-Provider Setup** | [MULTI_PROVIDER_SETUP.md](MULTI_PROVIDER_SETUP.md) | LLM provider configuration, API keys, model selection |
| **Advanced Features** | [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md) | ORDER BY, LIMIT, aggregations, spatial queries, caching |
| **Oil & Gas Compliance** | [OIL_GAS_LEASE_GUIDE.md](OIL_GAS_LEASE_GUIDE.md) | Compliance checking, rules, thresholds, reporting |
| **Session Management** | [SESSION_GUIDE.md](SESSION_GUIDE.md) | Save/load sessions, persistence, recovery |
| **Pagination** | [PAGINATION_ANALYSIS.md](PAGINATION_ANALYSIS.md) | Pagination strategy, performance, large datasets |

---

## API Reference

### Quick API Reference by Use Case

#### Querying Data

```python
from src.arcgis_client import ArcGISClient

client = ArcGISClient(service_url)

# Basic query
result = client.query(where="STATE_NAME = 'Texas'")

# Spatial query
result = client.query_nearby(
    point=(-97.7431, 30.2672),
    distance_miles=50
)

# Paginated query
result = client.query(
    where="1=1",
    page_size=100,
    max_pages=10
)
```

#### Natural Language Queries

```python
from src.nlp_query_parser import NLPQueryParser
from src.query_executor import execute_query

parser = NLPQueryParser(provider='anthropic')
parsed = parser.parse("find top 5 largest counties in Texas")
result = execute_query(client, parsed)
```

#### Compliance Checking

```python
from src.compliance_checker import ComplianceChecker, ComplianceRules

rules = ComplianceRules(max_area_sqmi=2500)
checker = ComplianceChecker(rules)
result = checker.check_compliance(lease_data)
```

#### Session Management

```python
from src.session_manager import SessionManager

manager = SessionManager()
session_id = manager.save_session(
    query_params={...},
    results=[...]
)
```

---

## Examples & Demos

### Production Examples

Located in `examples/` directory - production-ready scripts for oil & gas compliance.

| Example | File | Description |
|---------|------|-------------|
| **Basic Texas Compliance** | [01_basic_texas_compliance.py](../examples/01_basic_texas_compliance.py) | Basic compliance check for Texas counties |
| **Spatial Query Austin** | [02_spatial_query_austin.py](../examples/02_spatial_query_austin.py) | Find counties near Austin, TX |
| **Export Results** | [03_export_results.py](../examples/03_export_results.py) | Export to CSV/JSON formats |
| **Filter and Analyze** | [04_filter_and_analyze.py](../examples/04_filter_and_analyze.py) | Filter and detailed analysis |
| **Batch Multiple States** | [05_batch_multiple_states.py](../examples/05_batch_multiple_states.py) | Multi-state batch analysis |
| **Custom Thresholds** | [06_custom_thresholds.py](../examples/06_custom_thresholds.py) | Custom compliance rules |
| **Session Save/Load** | [07_session_save_load.py](../examples/07_session_save_load.py) | Session management demo |

**Running Examples:**
```bash
# See detailed instructions in:
# docs/SETUP_AND_DEMOS.md#running-examples
python3 examples/01_basic_texas_compliance.py
```

---

### Feature Demos

Located in root directory - demonstrations of new features.

| Demo | File | Features |
|------|------|----------|
| **NLP Query Parser** | [nlp_query_demo.py](../nlp_query_demo.py) | Natural language parsing, interactive mode |
| **Multi-Provider** | [multi_provider_demo.py](../multi_provider_demo.py) | Switch between LLM providers |
| **Advanced Queries** | [advanced_query_demo.py](../advanced_query_demo.py) | ORDER BY, LIMIT, aggregations, spatial |
| **Cache Demo** | [cache_demo.py](../cache_demo.py) | Query caching, performance, hit/miss stats |
| **Top 5 Test** | [test_top_5.py](../test_top_5.py) | Test top N queries |
| **Parser Quick Test** | [test_parser_quick.py](../test_parser_quick.py) | Quick parser test |

**Running Demos:**
```bash
# See detailed instructions in:
# docs/SETUP_AND_DEMOS.md#running-demos
python3 nlp_query_demo.py
python3 cache_demo.py
```

---

## Development

### Development Documentation

| Document | Description |
|----------|-------------|
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute code, coding standards |
| [STRUCTURE.md](STRUCTURE.md) | Project structure and architecture |
| [CHANGELOG.md](CHANGELOG.md) | Version history and changes |

### Testing

| Test File | Module Tested |
|-----------|---------------|
| `tests/test_arcgis_client.py` | ArcGIS client functionality |
| `tests/test_nlp_query_parser.py` | NLP query parser |
| `tests/test_compliance_checker.py` | Compliance checker |
| `tests/test_oil_gas_compliance.py` | Oil & gas compliance |
| `tests/test_session_manager.py` | Session manager |
| `tests/test_max_pages.py` | Pagination limits |

**Running Tests:**
```bash
# See detailed instructions in:
# docs/SETUP_AND_DEMOS.md#running-tests
pytest tests/ -v
pytest tests/test_arcgis_client.py -v
```

---

## Deployment

### Production Deployment

| Document | Description |
|----------|-------------|
| [README_PRODUCTION.md](README_PRODUCTION.md) | Complete production deployment guide |
| [PRODUCTION_UPGRADE.md](PRODUCTION_UPGRADE.md) | Recent production upgrades |
| [SETUP_AND_DEMOS.md](SETUP_AND_DEMOS.md) | Setup and verification |

**Key Topics:**
- Environment setup
- Configuration management
- Performance optimization
- Monitoring and logging
- Error handling
- Security considerations

---

## Search by Topic

### By Feature

| Feature | Documentation |
|---------|---------------|
| **Natural Language Queries** | [NLP_QUERY_PARSER_README.md](NLP_QUERY_PARSER_README.md), [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md) |
| **Caching** | [ADVANCED_FEATURES.md - Caching](ADVANCED_FEATURES.md#caching), [SETUP_AND_DEMOS.md - Cache Demo](SETUP_AND_DEMOS.md#cache-demo) |
| **Pagination** | [PAGINATION_ANALYSIS.md](PAGINATION_ANALYSIS.md), [README_PRODUCTION.md](README_PRODUCTION.md) |
| **Compliance Checking** | [OIL_GAS_LEASE_GUIDE.md](OIL_GAS_LEASE_GUIDE.md), Examples 01-06 |
| **Session Management** | [SESSION_GUIDE.md](SESSION_GUIDE.md), Example 07 |
| **Spatial Queries** | [ADVANCED_FEATURES.md - Spatial](ADVANCED_FEATURES.md#spatial-queries), Example 02 |
| **ORDER BY / LIMIT** | [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md), `test_top_5.py` |

### By Task

| Task | Documentation |
|------|---------------|
| **Setup Project** | [SETUP_AND_DEMOS.md - Initial Setup](SETUP_AND_DEMOS.md#initial-setup) |
| **Run Examples** | [SETUP_AND_DEMOS.md - Running Examples](SETUP_AND_DEMOS.md#running-examples) |
| **Configure LLM** | [MULTI_PROVIDER_SETUP.md](MULTI_PROVIDER_SETUP.md) |
| **Deploy to Production** | [README_PRODUCTION.md](README_PRODUCTION.md) |
| **Write Tests** | [CONTRIBUTING.md](CONTRIBUTING.md) |
| **Debug Issues** | [SETUP_AND_DEMOS.md - Troubleshooting](SETUP_AND_DEMOS.md#troubleshooting) |

### By Module

| Module | Documentation |
|--------|---------------|
| `src/arcgis_client.py` | [README_PRODUCTION.md](README_PRODUCTION.md), [PAGINATION_ANALYSIS.md](PAGINATION_ANALYSIS.md) |
| `src/nlp_query_parser.py` | [NLP_QUERY_PARSER_README.md](NLP_QUERY_PARSER_README.md), [MULTI_PROVIDER_SETUP.md](MULTI_PROVIDER_SETUP.md) |
| `src/llm_providers.py` | [MULTI_PROVIDER_SETUP.md](MULTI_PROVIDER_SETUP.md) |
| `src/query_executor.py` | [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md) |
| `src/compliance_checker.py` | [OIL_GAS_LEASE_GUIDE.md](OIL_GAS_LEASE_GUIDE.md) |
| `src/session_manager.py` | [SESSION_GUIDE.md](SESSION_GUIDE.md) |

---

## Document Relationships

```
README.md (Main)
    ├── SETUP_AND_DEMOS.md ────────────► Start here for setup
    │       ├── Run all examples
    │       ├── Run all demos
    │       └── Run tests
    │
    ├── DOCUMENTATION_INDEX.md ────────► This file - central index
    │
    └── Module-Specific Docs:
            ├── NLP_QUERY_PARSER_README.md
            ├── MULTI_PROVIDER_SETUP.md
            ├── ADVANCED_FEATURES.md
            ├── OIL_GAS_LEASE_GUIDE.md
            ├── SESSION_GUIDE.md
            ├── PAGINATION_ANALYSIS.md
            ├── README_PRODUCTION.md
            └── PRODUCTION_UPGRADE.md
```

---

## Contributing to Documentation

Found missing documentation or want to improve it?

1. Check [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines
2. Follow existing documentation format
3. Update this index when adding new docs
4. Test all code examples still work
5. Update "Last Updated" date

---

## Documentation Standards

All documentation follows:
- ✅ Markdown format with consistent formatting
- ✅ Clear section headers and table of contents
- ✅ Code examples with syntax highlighting
- ✅ Links to related resources
- ✅ Runnable code examples (verified)
- ✅ Updated "Last Updated" dates

---

**Last Updated**: 2025-12-02
