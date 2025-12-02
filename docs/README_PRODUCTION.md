# ArcGIS Client - Production-Grade Implementation

[![CI/CD](https://github.com/yourusername/arcgis-client/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/yourusername/arcgis-client/actions)
[![codecov](https://codecov.io/gh/yourusername/arcgis-client/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/arcgis-client)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A production-grade, enterprise-ready Python client for ArcGIS Feature Services with advanced features including compliance checking, session management, comprehensive logging, and robust error handling.

## ✨ Features

### Core Functionality
- **ArcGIS Integration**: Full-featured client for ArcGIS Feature Services
- **Spatial Queries**: Support for both attribute and spatial queries
- **GeoJSON Support**: Automatic conversion to/from GeoJSON format
- **Pagination**: Automatic pagination for large datasets
- **Compliance Checking**: Built-in area compliance verification

### Production Features
- **Structured Logging**: JSON-formatted logs with contextual information
- **Configuration Management**: Environment-based configuration with validation
- **Retry Logic**: Exponential backoff for failed requests
- **Connection Pooling**: HTTP connection reuse for better performance
- **Session Management**: Atomic file operations with automatic backups
- **Error Handling**: Hierarchical exception handling with detailed messages
- **Type Safety**: Comprehensive type hints throughout
- **Security**: Input validation, secrets management, security scanning

### Developer Experience
- **Pre-commit Hooks**: Automatic code formatting and linting
- **CI/CD Pipeline**: Automated testing and deployment
- **Docker Support**: Containerized deployment ready
- **Makefile**: Common development tasks automated
- **Comprehensive Tests**: Unit and integration test coverage
- **Documentation**: Detailed API and usage documentation

## 📋 Requirements

- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/arcgis-client.git
cd arcgis-client

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or install with development tools
make install-dev
```

### Basic Usage

```python
from arcgis_client import ArcGISClient

# Initialize client
service_url = "https://services.arcgis.com/.../FeatureServer/0"
with ArcGISClient(service_url) as client:
    # Attribute query
    features = client.query(where="STATE_NAME = 'Texas'")
    print(f"Found {len(features['features'])} features")

    # Spatial query
    nearby = client.query_nearby(
        point=(-97.7431, 30.2672),
        distance_miles=50
    )
```

## 📖 Comprehensive Usage

### Configuration

Create a `.env` file from the template:

```bash
make setup-env
```

Configure your environment variables in `.env`:

```bash
# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE_PATH=logs/app.log

# Network
ARCGIS_CONNECT_TIMEOUT=10
ARCGIS_READ_TIMEOUT=30
ARCGIS_MAX_RETRIES=3

# Cache
ARCGIS_CACHE_ENABLED=true
ARCGIS_CACHE_TTL=300
```

### Advanced Client Usage

```python
from arcgis_client import SimpleArcGISClient, ArcGISClient
from logger import get_logger
from config import get_config

logger = get_logger(__name__)
config = get_config()

# Using context manager for automatic resource cleanup
with ArcGISClient(service_url) as client:
    # Attribute query with pagination
    texas_counties = client.query(
        where="STATE_NAME = 'Texas'",
        page_size=500,
        paginate=True
    )

    # Spatial query with custom distance
    results = client.query_nearby(
        point=(-104.0, 39.0),
        distance_miles=5.0,
        where="POPULATION > 10000",
        spatial_relationship="esriSpatialRelWithin"
    )

    # Low-level API access
    simple_client = SimpleArcGISClient(service_url)
    data = simple_client.query_features(
        where_clause="1=1",
        max_records=100,
        out_fields="NAME,POPULATION,SQMI",
        return_geometry=True
    )
```

### Compliance Checking

```python
from compliance_checker import check_area_compliance, generate_shortfall_report

# Check area compliance
report = check_area_compliance(
    features=geojson_data['features'],
    min_area_sq_miles=1000.0
)

print(f"Compliant: {report['compliant_count']}")
print(f"Non-compliant: {report['non_compliant_count']}")

# Generate detailed shortfall report
detailed_report = generate_shortfall_report(
    features=geojson_data['features'],
    min_area_sq_miles=1000.0
)
```

### Session Management

```python
from session_manager import SessionManager

# Initialize with auto-backup enabled
manager = SessionManager(
    filepath="sessions/analysis.json",
    auto_backup=True
)

# Save session
manager.save_session(
    query_params={"where": "STATE='CA'"},
    query_results=features,
    compliance_report=report,
    user="analyst@example.com"
)

# Load session
loaded_session = manager.load_session()
print(f"User: {loaded_session['meta']['user']}")
print(f"Timestamp: {loaded_session['meta']['timestamp']}")
```

## 🛠️ Development

### Setup Development Environment

```bash
# Initialize development environment
make init

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests with coverage
make test

# Run specific test file
pytest tests/test_arcgis_client.py -v

# Run integration tests (requires network)
make test-integration

# Generate coverage report
make coverage-report
```

### Code Quality

```bash
# Format code
make format

# Run linters
make lint

# Security checks
make security

# Run all checks
make check-all
```

### Available Make Commands

```bash
make help              # Show all available commands
make install           # Install production dependencies
make install-dev       # Install development dependencies
make test              # Run tests with coverage
make lint              # Run linters
make format            # Format code
make security          # Run security checks
make clean             # Clean build artifacts
make run               # Run main application
make build             # Build distribution packages
make docker-build      # Build Docker image
```

## 🐳 Docker Deployment

### Build and Run with Docker

```bash
# Build Docker image
make docker-build

# Run with Docker
docker run --rm -it \
  -e LOG_LEVEL=INFO \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/sessions:/app/sessions \
  arcgis-client:latest
```

### Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📊 Project Structure

```
arcgis-client/
├── .github/
│   └── workflows/
│       └── ci.yml              # CI/CD pipeline
├── tests/                      # Unit and integration tests
│   ├── test_arcgis_client.py
│   ├── test_compliance_checker.py
│   └── test_session_manager.py
├── examples/                   # Usage examples
│   ├── usage_examples.py
│   └── sample_session.json
├── logs/                       # Application logs
├── sessions/                   # Saved sessions
├── arcgis_client.py           # Main ArcGIS client
├── compliance_checker.py      # Compliance logic
├── session_manager.py         # Session management
├── config.py                  # Configuration management
├── logger.py                  # Logging setup
├── errors.py                  # Custom exceptions
├── main.py                    # Demo application
├── requirements.txt           # Dependencies
├── setup.py                   # Package setup
├── pyproject.toml            # Modern Python packaging
├── Dockerfile                # Container definition
├── docker-compose.yml        # Multi-container setup
├── Makefile                  # Development automation
├── .env.example              # Environment template
├── .gitignore                # Git ignore rules
├── .pre-commit-config.yaml   # Pre-commit hooks
├── CONTRIBUTING.md           # Contribution guidelines
└── README.md                 # This file
```

## 🔧 Configuration Options

### Logging Configuration
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `LOG_FORMAT`: Log format (json, text)
- `LOG_FILE_PATH`: Path to log file
- `LOG_MAX_BYTES`: Maximum log file size
- `LOG_BACKUP_COUNT`: Number of backup log files

### Network Configuration
- `ARCGIS_CONNECT_TIMEOUT`: Connection timeout in seconds
- `ARCGIS_READ_TIMEOUT`: Read timeout in seconds
- `ARCGIS_MAX_RETRIES`: Maximum retry attempts
- `ARCGIS_RETRY_BACKOFF`: Backoff factor for retries
- `ARCGIS_MAX_CONNECTIONS`: Maximum connection pool size

### Cache Configuration
- `ARCGIS_CACHE_ENABLED`: Enable/disable caching
- `ARCGIS_CACHE_TTL`: Cache TTL in seconds
- `ARCGIS_CACHE_MAX_SIZE`: Maximum cache entries

### Query Configuration
- `ARCGIS_DEFAULT_PAGE_SIZE`: Default pagination size
- `ARCGIS_MAX_PAGE_SIZE`: Maximum page size
- `ARCGIS_ENABLE_PAGINATION`: Enable automatic pagination

## 🔒 Security

### Best Practices
- Never commit `.env` files or secrets
- Use environment variables for sensitive data
- Regularly update dependencies: `make update-deps`
- Run security checks: `make security`
- Review security advisories

### Security Scanning
```bash
# Run bandit (security linter)
bandit -r . -x tests,.venv

# Check dependencies
safety check
```

## 📈 Performance

### Optimizations Included
- **Connection Pooling**: Reuses HTTP connections
- **Automatic Pagination**: Efficiently handles large datasets
- **Request Retry**: Exponential backoff for failed requests
- **Lazy Loading**: Resources loaded on demand
- **Caching**: Optional response caching

### Performance Tips
```python
# Use context managers for automatic cleanup
with ArcGISClient(url) as client:
    results = client.query(where="1=1")

# Adjust page size based on your needs
client.query(where="1=1", page_size=2000)

# Disable pagination for small queries
client.query(where="ID=123", paginate=False)
```

## 🧪 Testing

### Test Coverage
- Unit tests for all core functionality
- Integration tests for live service interaction
- Mock-based tests for offline development
- Security and performance tests

### Running Specific Tests
```bash
# Run with markers
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m slow          # Slow tests

# Run with specific test
pytest tests/test_arcgis_client.py::TestArcGISClient::test_query_success
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Contribution Steps
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and checks: `make check-all`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- ArcGIS REST API documentation
- Python community for excellent libraries
- Contributors and users of this project

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/arcgis-client/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/arcgis-client/discussions)
- **Email**: dev@example.com

## 🗺️ Roadmap

- [ ] Async/await support for concurrent requests
- [ ] GraphQL API support
- [ ] Advanced caching strategies (Redis, Memcached)
- [ ] Real-time feature updates via WebSockets
- [ ] CLI tool for common operations
- [ ] Web dashboard for monitoring

---

**Built with ❤️ for the GIS community**
