# Session Save/Load Guide

## Overview

The `SessionManager` allows you to save and resume analysis sessions, enabling:
- **Resume work later** - Save your analysis and continue tomorrow
- **Share results** - Send session files to colleagues
- **Audit trail** - Track who ran what analysis and when
- **Backup protection** - Automatic backups prevent data loss

---

## Quick Start

### Basic Save/Load

```python
from arcgis_client import ArcGISClient
from compliance_checker import analyze_oil_gas_lease_compliance
from session_manager import SessionManager

# Run analysis
client = ArcGISClient(service_url)
results = client.query(where="STATE_NAME = 'Texas'")
report = analyze_oil_gas_lease_compliance(results['features'])

# Save session
session_mgr = SessionManager(filepath="my_session.json")
session_mgr.save_session(
    query_params={"where": "STATE_NAME = 'Texas'"},
    query_results=results,
    compliance_report=report,
    user="john_doe"
)

# Load session (later or on another machine)
loaded = session_mgr.load_session()
print(f"Loaded {len(loaded['results']['features'])} features")
print(f"Compliance rate: {loaded['report']['summary']['compliance_rate_percentage']}%")
```

---

## Running the Examples

### Example 7: Full Session Workflow

```bash
# Create new session (runs analysis and saves)
python3 examples/07_session_save_load.py

# Load existing session only
python3 examples/07_session_save_load.py --load-only

# Custom session file location
python3 examples/07_session_save_load.py --session-file=my_analysis.json

# Disable automatic backups
python3 examples/07_session_save_load.py --no-backup

# Specify user for audit trail
python3 examples/07_session_save_load.py --user=alice_smith
```

### Quick Unit Test

```bash
# Test save/load without network calls
python3 test_session_manager.py
```

---

## Session File Structure

Saved sessions use JSON format with this structure:

```json
{
  "meta": {
    "user": "john_doe",
    "timestamp": "2025-12-02T14:30:45.123456",
    "version": "1.0"
  },
  "query_params": {
    "where": "STATE_NAME = 'Texas'",
    "page_size": 500,
    "min_area_sq_miles": 2500.0
  },
  "results": {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "geometry": {...},
        "properties": {
          "NAME": "Harris",
          "SQMI": 1700.5,
          ...
        }
      },
      ...
    ]
  },
  "report": {
    "summary": {
      "total_counties_analyzed": 254,
      "compliant_count": 9,
      "non_compliant_count": 245,
      "compliance_rate_percentage": 3.54
    },
    "non_compliant_counties": [...],
    "compliant_counties": [...],
    "metadata": {...}
  }
}
```

---

## Features

### 1. Automatic Backups

When enabled, SessionManager creates timestamped backups before overwriting:

```python
# Enable automatic backups (default)
session_mgr = SessionManager(filepath="session.json", auto_backup=True)

# Saves create backups like:
# session.json.20251202_143045.bak
# session.json.20251202_150122.bak
# session.json.20251202_153200.bak
```

**Backup retention**: Configured via `config.session.backup_count` (default: 5)

### 2. Atomic Writes

Sessions are written atomically to prevent corruption:

1. Write to temporary file: `session.json.tmp`
2. Atomic rename: `session.json.tmp` → `session.json`
3. Guarantees file is never partially written

### 3. Audit Trail

Every session includes metadata:
- **user**: Who created the session
- **timestamp**: When it was created (ISO 8601 format)
- **version**: Session format version

### 4. Structured Logging

All operations are logged with structured data:

```json
{
  "timestamp": "2025-12-02T14:30:45.123456Z",
  "level": "INFO",
  "logger": "session_manager",
  "message": "Session saved successfully",
  "filepath": "/path/to/session.json",
  "size_bytes": 125643
}
```

---

## Use Cases

### 1. Long-Running Analysis

```python
# Day 1: Run partial analysis
session_mgr = SessionManager("texas_analysis.json")
results = client.query(where="STATE_NAME = 'Texas'")
report = analyze_oil_gas_lease_compliance(results['features'])
session_mgr.save_session(..., user="analyst_1")

# Day 2: Resume and extend
loaded = session_mgr.load_session()
# Use loaded data to continue analysis
```

### 2. Share Results with Team

```python
# Analyst runs query
session_mgr.save_session(..., user="data_team")

# Email session.json to manager
# Manager loads and reviews:
loaded = session_mgr.load_session()
print(f"Analysis by: {loaded['meta']['user']}")
print(f"Date: {loaded['meta']['timestamp']}")
# Review compliance_report
```

### 3. Audit and Compliance

```python
# Track who ran what analysis
for session_file in glob("sessions/*.json"):
    session = SessionManager(session_file).load_session()
    print(f"{session['meta']['user']}: {session['meta']['timestamp']}")
    print(f"  Query: {session['query_params']['where']}")
    print(f"  Results: {len(session['results']['features'])} features")
```

### 4. Regression Testing

```python
# Save baseline results
baseline_mgr = SessionManager("baseline_v1.0.json")
baseline_mgr.save_session(..., user="regression_test")

# After code changes, compare
new_results = run_analysis()
baseline = baseline_mgr.load_session()

# Verify results match
assert len(new_results['features']) == len(baseline['results']['features'])
assert new_results['summary'] == baseline['report']['summary']
```

---

## Configuration

Configure via environment variables or `config.py`:

```python
# config.py
@dataclass
class SessionConfig:
    auto_backup: bool = field(default=True)
    backup_count: int = field(default=5)  # Keep last 5 backups
```

**Environment Variables**:
```bash
export SESSION_AUTO_BACKUP=false  # Disable backups
export SESSION_BACKUP_COUNT=10    # Keep 10 backups
```

---

## API Reference

### SessionManager

#### `__init__(filepath, auto_backup=None)`

Initialize session manager.

**Args**:
- `filepath` (str): Path to session file
- `auto_backup` (bool, optional): Enable backups (default: from config)

#### `save_session(query_params, query_results, compliance_report, user="default_user")`

Save analysis session.

**Args**:
- `query_params` (dict): Query parameters used
- `query_results` (dict): GeoJSON FeatureCollection
- `compliance_report` (dict): Compliance analysis report
- `user` (str): User identifier

**Returns**: Absolute path to saved file

**Raises**:
- `SessionManagerError`: If save fails

#### `load_session()`

Load saved session.

**Returns**: Dict with keys: `meta`, `query_params`, `results`, `report`

**Raises**:
- `FileNotFoundError`: If session file doesn't exist
- `json.JSONDecodeError`: If file is corrupted
- `SessionManagerError`: If read fails

---

## Testing

### Unit Tests

```bash
# Test basic functionality (fast, no network)
python3 test_session_manager.py

# Expected output:
# ✓ Save Session
# ✓ Load Session
# ✓ Verify Data Integrity
# ✓ Test Backup Creation
# ✓ Verify Updated Data
# ✅ ALL TESTS PASSED!
```

### Integration Test

```bash
# Test with real ArcGIS query (requires internet)
python3 examples/07_session_save_load.py

# Verify:
# ✓ Analysis runs successfully
# ✓ Session saves to file
# ✓ Session loads correctly
# ✓ Data integrity verified
```

---

## Troubleshooting

### FileNotFoundError

```
Error: Session file session.json not found
```

**Solution**: Run analysis first to create session, or check file path.

### JSONDecodeError

```
Error: Invalid JSON in session file
```

**Solution**: File is corrupted. Restore from backup:
```bash
cp session.json.20251202_143045.bak session.json
```

### Permission Denied

```
Error: Failed to write session to /protected/path/session.json
```

**Solution**: Check directory permissions or use writable location:
```python
session_mgr = SessionManager(filepath="~/sessions/my_session.json")
```

---

## Best Practices

### 1. Use Descriptive Filenames

```python
# Good
SessionManager("texas_compliance_2025-12-02.json")

# Bad
SessionManager("session.json")
```

### 2. Always Specify User

```python
# Good
session_mgr.save_session(..., user="alice@company.com")

# Avoid
session_mgr.save_session(...)  # Uses "default_user"
```

### 3. Organize Sessions

```
sessions/
├── 2025-12/
│   ├── texas_compliance_2025-12-01.json
│   ├── texas_compliance_2025-12-02.json
│   └── multi_state_2025-12-02.json
└── archived/
    └── 2025-11/
```

### 4. Keep Backups Enabled

```python
# Production: Always use backups
session_mgr = SessionManager(filepath="prod_session.json", auto_backup=True)

# Development/Testing: Can disable for speed
session_mgr = SessionManager(filepath="test_session.json", auto_backup=False)
```

### 5. Version Your Sessions

Add version info to query_params for tracking:

```python
query_params = {
    "where": "STATE_NAME = 'Texas'",
    "analysis_version": "2.1.0",
    "notes": "Updated compliance thresholds"
}
```

---

## Examples Summary

| Example | Purpose | Network Required | Time |
|---------|---------|------------------|------|
| `test_session_manager.py` | Unit test with mock data | No | ~1s |
| `examples/07_session_save_load.py` | Full workflow with real data | Yes | ~10s |
| `examples/07_session_save_load.py --load-only` | Load existing session | No | <1s |

---

## See Also

- **Session Manager Source**: `session_manager.py`
- **Configuration**: `config.py` → `SessionConfig`
- **Error Handling**: `errors.py` → `SessionManagerError`
- **Logging**: `logger.py`
- **Example Script**: `examples/07_session_save_load.py`
- **Unit Tests**: `test_session_manager.py`
