# Project Structure

Clean, organized directory structure for production-grade GIS development.

```
gis-developer-takehome/
│
├── src/                          # 🔧 Core Source Code
│   ├── __init__.py              # Package initialization & exports
│   ├── arcgis_client.py         # ArcGIS Feature Service client
│   ├── compliance_checker.py    # Business rule compliance analysis
│   ├── session_manager.py       # Session save/load functionality
│   ├── config.py                # Configuration management
│   ├── logger.py                # Structured logging
│   └── errors.py                # Custom exceptions
│
├── examples/                     # 📝 Example Scripts
│   ├── README.md                # Examples documentation
│   ├── 01_basic_texas_compliance.py
│   ├── 02_spatial_query_austin.py
│   ├── 03_export_results.py
│   ├── 04_filter_and_analyze.py
│   ├── 05_batch_multiple_states.py
│   ├── 06_custom_thresholds.py
│   ├── 07_session_save_load.py
│   ├── output/                  # Generated export files
│   └── sessions/                # Saved session files
│
├── tests/                        # 🧪 Test Suite
│   ├── __init__.py
│   ├── test_arcgis_client.py
│   ├── test_compliance_checker.py
│   ├── test_oil_gas_compliance.py
│   ├── test_session_manager.py
│   └── test_max_pages.py
│
├── docs/                         # 📚 Documentation
│   ├── README.md                # Documentation index
│   ├── README_PRODUCTION.md     # Production deployment guide
│   ├── PRODUCTION_UPGRADE.md    # Upgrade details
│   ├── OIL_GAS_LEASE_GUIDE.md  # API & usage guide
│   ├── SESSION_GUIDE.md         # Session management guide
│   ├── PAGINATION_ANALYSIS.md   # Pagination implementation
│   ├── EXAMPLES_SUMMARY.md      # Examples quick reference
│   ├── CONTRIBUTING.md          # Contribution guidelines
│   └── CHANGELOG.md             # Version history
│
├── logs/                         # 📊 Log Files
│   └── app.log                  # Application logs (JSON format)
│
├── .github/                      # ⚙️ GitHub Configuration
│   └── workflows/
│       └── ci.yml               # CI/CD pipeline
│
├── README.md                     # 📖 Main Project README
├── STRUCTURE.md                  # 📂 This file
├── requirements.txt              # 📦 Python dependencies
├── setup.py                      # 📦 Package setup
├── pyproject.toml               # 🔧 Python project config
├── Makefile                      # 🛠️ Build automation
├── Dockerfile                    # 🐳 Docker configuration
├── docker-compose.yml           # 🐳 Docker Compose setup
├── .gitignore                   # 🚫 Git ignore rules
├── .env.example                 # 🔐 Environment variables template
├── main.py                       # 🚀 Main entry point
└── oil_gas_lease_demo.py        # 🎯 Oil & gas demo script
```

---

## 📂 Directory Purposes

### **src/** - Core Application Code
Contains all production source code organized by functionality.

**Key Files:**
- `arcgis_client.py` - ArcGIS REST API client with pagination
- `compliance_checker.py` - Business rule validation engine
- `session_manager.py` - Analysis session persistence
- `config.py` - Centralized configuration
- `logger.py` - Structured JSON logging
- `errors.py` - Custom exception hierarchy

**Import from src:**
```python
from src.arcgis_client import ArcGISClient
from src.compliance_checker import analyze_oil_gas_lease_compliance
from src.session_manager import SessionManager
```

---

### **examples/** - Runnable Examples
Real-world usage examples demonstrating all features.

**Categories:**
1. **Basic** - `01_basic_texas_compliance.py`
2. **Spatial** - `02_spatial_query_austin.py`
3. **Export** - `03_export_results.py`
4. **Filtering** - `04_filter_and_analyze.py`
5. **Batch** - `05_batch_multiple_states.py`
6. **Scenarios** - `06_custom_thresholds.py`
7. **Sessions** - `07_session_save_load.py`

**Run examples:**
```bash
python3 examples/01_basic_texas_compliance.py
python3 examples/07_session_save_load.py --help
```

---

### **tests/** - Test Suite
Comprehensive test coverage for all modules.

**Test Types:**
- Unit tests - Individual function testing
- Integration tests - End-to-end workflows
- Mock tests - Network-free testing

**Run tests:**
```bash
pytest tests/
pytest tests/test_session_manager.py -v
make test
```

---

### **docs/** - Documentation
Complete project documentation organized by topic.

**Document Types:**
- **Guides** - How-to documentation
- **References** - API documentation
- **Analysis** - Technical deep-dives
- **Meta** - Contributing, changelog

**Browse docs:**
```bash
cd docs/
ls -la
cat README.md
```

---

### **logs/** - Application Logs
Structured JSON logs for production monitoring.

**Log Format:**
```json
{
  "timestamp": "2025-12-02T14:30:45.123456Z",
  "level": "INFO",
  "logger": "arcgis_client",
  "message": "Feature query completed",
  "total_features": 254,
  "duration_ms": 1234.5
}
```

---

## 🎯 Quick Navigation

### **I want to...**

#### Use the Library
→ Start here: `README.md`
→ See examples: `examples/README.md`
→ API docs: `docs/OIL_GAS_LEASE_GUIDE.md`

#### Develop/Contribute
→ Setup: `docs/CONTRIBUTING.md`
→ Source code: `src/`
→ Tests: `tests/`

#### Deploy to Production
→ Guide: `docs/README_PRODUCTION.md`
→ Docker: `Dockerfile`, `docker-compose.yml`
→ CI/CD: `.github/workflows/ci.yml`

#### Understand Architecture
→ Upgrade details: `docs/PRODUCTION_UPGRADE.md`
→ Pagination: `docs/PAGINATION_ANALYSIS.md`
→ Sessions: `docs/SESSION_GUIDE.md`

---

## 📦 Module Organization

### Import Hierarchy

```python
# Top-level package
import src

# Sub-modules
from src import arcgis_client
from src import compliance_checker
from src import session_manager

# Specific classes/functions
from src.arcgis_client import ArcGISClient
from src.compliance_checker import analyze_oil_gas_lease_compliance
from src.session_manager import SessionManager
```

### Package Dependencies

```
src.arcgis_client
├── depends on: src.errors, src.logger, src.config
└── provides: ArcGISClient, SimpleArcGISClient

src.compliance_checker
├── depends on: src.errors, src.logger
└── provides: analyze_oil_gas_lease_compliance, check_area_compliance

src.session_manager
├── depends on: src.errors, src.logger, src.config
└── provides: SessionManager
```

---

## 🔧 Configuration Files

| File | Purpose | Location |
|------|---------|----------|
| `requirements.txt` | Python dependencies | Root |
| `setup.py` | Package installation | Root |
| `pyproject.toml` | Modern Python config | Root |
| `.env.example` | Environment template | Root |
| `Makefile` | Build automation | Root |
| `Dockerfile` | Container definition | Root |
| `docker-compose.yml` | Multi-container setup | Root |

---

## 🚀 Entry Points

### Command Line
```bash
# Main application
python3 main.py

# Oil & gas demo
python3 oil_gas_lease_demo.py

# Examples
python3 examples/01_basic_texas_compliance.py

# Tests
pytest tests/
```

### Python API
```python
# As a library
from src.arcgis_client import ArcGISClient
from src.compliance_checker import analyze_oil_gas_lease_compliance

# Use in your code
client = ArcGISClient(service_url)
results = client.query(where="STATE_NAME = 'Texas'")
report = analyze_oil_gas_lease_compliance(results['features'])
```

### Docker
```bash
# Build
docker-compose build

# Run
docker-compose up

# Execute tests
docker-compose run app pytest
```

---

## 📊 Generated Files/Directories

These directories are created at runtime:

```
examples/
├── output/               # Created by example 03
│   ├── *.json
│   ├── *.csv
│   └── *.txt
└── sessions/            # Created by example 07
    └── *.json

logs/
└── app.log              # Created by logger

*.pyc                    # Python bytecode
__pycache__/            # Python cache
.pytest_cache/          # Pytest cache
*.egg-info/             # Package metadata
```

Add to `.gitignore`:
```gitignore
examples/output/
examples/sessions/
logs/
__pycache__/
*.pyc
*.egg-info/
.pytest_cache/
```

---

## 🔄 Migration from Old Structure

If upgrading from previous structure:

```bash
# Old structure (all in root)
arcgis_client.py       → src/arcgis_client.py
compliance_checker.py  → src/compliance_checker.py
test_*.py              → tests/test_*.py
*.md                   → docs/*.md

# Update imports in your code
from arcgis_client import ArcGISClient
# becomes
from src.arcgis_client import ArcGISClient
```

---

## ✅ Best Practices

### **DO:**
- ✅ Import from `src.` prefix
- ✅ Run examples from project root
- ✅ Add new docs to `docs/`
- ✅ Add new tests to `tests/`
- ✅ Keep logs in `logs/`

### **DON'T:**
- ❌ Import without `src.` prefix
- ❌ Put source code in root
- ❌ Mix docs with code
- ❌ Commit generated files

---

**Structure Version**: 2.0
**Last Updated**: 2025-12-02
