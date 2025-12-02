"""
Detect discrepancies between GIS-provided county areas and a reference database.

The detector compares the SQMI attribute on GIS features against a SQLite-backed
reference table and flags records where the percent difference exceeds a
configurable tolerance.
"""

import sqlite3
from typing import Any, Dict, List, Tuple

from src.errors import DiscrepancyError
from src.logger import get_logger

logger = get_logger(__name__)


def seed_reference_database(
    db_path: str,
    county_rows: List[Dict[str, Any]],
    table_name: str = "county_reference"
) -> str:
    """
    Create or refresh a SQLite reference table with county area values.

    Args:
        db_path: Path to the SQLite database file.
        county_rows: List of dictionaries containing 'name', optional 'state',
                     and 'sqmi' keys.
        table_name: Name of the table to create/replace. Default: county_reference.

    Returns:
        The path to the seeded database file.

    Raises:
        DiscrepancyError: If inputs are invalid or database operations fail.
    """
    if not isinstance(county_rows, list) or not county_rows:
        raise DiscrepancyError("county_rows must be a non-empty list.")

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    name TEXT NOT NULL,
                    state TEXT,
                    sqmi REAL NOT NULL,
                    PRIMARY KEY (name, state)
                )
                """
            )
            cursor.execute(f"DELETE FROM {table_name}")
            records: List[Tuple[str, str, float]] = []
            for row in county_rows:
                name = row.get("name")
                if not name:
                    raise DiscrepancyError("Each row must include a county 'name'.")
                try:
                    sqmi = float(row.get("sqmi"))
                except (TypeError, ValueError):
                    raise DiscrepancyError(f"Invalid sqmi value for {name!r}.")
                state = row.get("state") or ""
                records.append((name, state, sqmi))

            cursor.executemany(
                f"INSERT OR REPLACE INTO {table_name} (name, state, sqmi) VALUES (?, ?, ?)",
                records,
            )
            conn.commit()
            logger.info(
                "Seeded reference database",
                extra={"row_count": len(records), "table": table_name, "db_path": db_path},
            )
    except sqlite3.Error as exc:
        logger.error("Failed to seed reference database", exc_info=True)
        raise DiscrepancyError(f"Database error: {exc}") from exc

    return db_path


def detect_area_discrepancies(
    features: List[Dict[str, Any]],
    db_path: str,
    table_name: str = "county_reference",
    tolerance_percent: float = 1.0,
) -> Dict[str, Any]:
    """
    Compare GIS feature areas against a SQLite reference table and flag discrepancies.

    Args:
        features: GIS features containing 'attributes' or 'properties' with NAME, STATE_NAME, SQMI.
        db_path: Path to SQLite database holding reference county areas.
        table_name: Table storing reference data with columns (name, state, sqmi).
        tolerance_percent: Allowed percent difference before flagging (absolute). Default: 1.0%.

    Returns:
        Dictionary summarizing comparison results and any flagged discrepancies.

    Raises:
        DiscrepancyError: When inputs are invalid or the database cannot be read.
    """
    if not isinstance(features, list):
        raise DiscrepancyError("features must be provided as a list.")
    if tolerance_percent < 0:
        raise DiscrepancyError("tolerance_percent must be non-negative.")

    reference = _load_reference_map(db_path, table_name)
    results: Dict[str, Any] = {
        "tolerance_percent": tolerance_percent,
        "compared": 0,
        "flagged_count": 0,
        "matching_count": 0,
        "invalid_features": 0,
        "missing_in_db": [],
        "discrepancies": [],
        "matches": [],
    }

    for feature in features:
        attrs = feature.get("attributes") or feature.get("properties") or {}
        name = attrs.get("NAME")
        state = attrs.get("STATE_NAME", "") or ""

        try:
            gis_sqmi = float(attrs.get("SQMI"))
        except (TypeError, ValueError):
            results["invalid_features"] += 1
            logger.warning(
                "Invalid GIS area encountered",
                extra={"county_name": name, "state": state},
            )
            continue

        if not name:
            results["invalid_features"] += 1
            logger.warning("Missing county name on GIS feature", extra={"state": state})
            continue

        key = (name.strip().lower(), state.strip().lower())
        if key not in reference:
            results["missing_in_db"].append(name)
            logger.info(
                "GIS feature not found in reference database",
                extra={"county_name": name, "state": state},
            )
            continue

        db_sqmi = reference[key]
        results["compared"] += 1

        if db_sqmi == 0:
            results["invalid_features"] += 1
            logger.warning("Reference area is zero; skipping comparison", extra={"name": name, "state": state})
            continue

        percent_diff = ((gis_sqmi - db_sqmi) / db_sqmi) * 100
        difference_sqmi = gis_sqmi - db_sqmi
        is_flagged = abs(percent_diff) > tolerance_percent

        detail = {
            "name": name,
            "state": state or None,
            "gis_sq_miles": round(gis_sqmi, 2),
            "db_sq_miles": round(db_sqmi, 2),
            "difference_sq_miles": round(difference_sqmi, 2),
            "percent_difference": round(percent_diff, 2),
            "status": "GIS higher" if difference_sqmi > 0 else "GIS lower",
        }

        if is_flagged:
            results["flagged_count"] += 1
            results["discrepancies"].append(detail)
            logger.info(
                "Discrepancy detected",
                extra={
                    "county_name": name,
                    "state": state,
                    "percent_difference": detail["percent_difference"],
                    "tolerance_percent": tolerance_percent,
                },
            )
        else:
            results["matching_count"] += 1
            results["matches"].append(detail)

    return results


def _load_reference_map(db_path: str, table_name: str) -> Dict[Tuple[str, str], float]:
    """Load county areas from SQLite into a lookup map keyed by (name, state)."""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT name, state, sqmi FROM {table_name}")
            rows = cursor.fetchall()
    except sqlite3.Error as exc:
        logger.error("Failed to read reference database", exc_info=True)
        raise DiscrepancyError(f"Unable to read reference table: {exc}") from exc

    reference: Dict[Tuple[str, str], float] = {}
    for name, state, sqmi in rows:
        if name is None:
            continue
        key = (str(name).strip().lower(), str(state or "").strip().lower())
        try:
            reference[key] = float(sqmi)
        except (TypeError, ValueError):
            logger.warning("Skipping reference row with invalid sqmi", extra={"name": name, "state": state})
            continue

    return reference
