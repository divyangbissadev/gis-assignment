import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from src.errors import SessionManagerError
from src.logger import get_logger
from src.config import get_config

logger = get_logger(__name__)

class SessionManager:
    """
    Manages saving and loading of analysis sessions with atomic writes.

    Features:
    - Atomic file writes using temporary files
    - Automatic backup creation
    - Structured logging for audit trail
    - Configuration-driven defaults
    """

    def __init__(self, session_dir: str = "sessions", auto_backup: Optional[bool] = None) -> None:
        """
        Initialize the session manager.

        Args:
            session_dir: Path to the directory where session files will be stored.
            auto_backup: Enable automatic backups. If None, uses config default.
        """
        self.session_dir = Path(session_dir)
        self.config = get_config()
        self.auto_backup = auto_backup if auto_backup is not None else self.config.session.auto_backup

        # Ensure the session directory exists
        self.session_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Session manager initialized",
            extra={
                "session_dir": str(self.session_dir),
                "auto_backup": self.auto_backup,
            }
        )

    def _get_session_path(self, name: str) -> Path:
        """
        Constructs the full file path for a given session name.

        Args:
            name: The name of the session.

        Returns:
            A Path object representing the full path to the session file.
        """
        if not name:
            raise ValueError("Session name cannot be empty.")
        # Ensure the session directory exists
        self.session_dir.mkdir(parents=True, exist_ok=True)
        return self.session_dir / f"{name}.json"

    def _create_backup(self, session_filepath: Path) -> None:
        """Create a backup of the existing session file."""
        if not session_filepath.exists():
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = session_filepath.parent / f"{session_filepath.name}.{timestamp}.bak"
            shutil.copy2(session_filepath, backup_path)

            logger.info("Session backup created", extra={"backup_path": str(backup_path)})

            self._cleanup_old_backups(session_filepath)

        except OSError as e:
            logger.warning(
                "Failed to create backup",
                extra={"filepath": str(session_filepath), "error": str(e)}
            )

    def _cleanup_old_backups(self, session_filepath: Path) -> None:
        """Remove old backup files keeping only the most recent ones."""
        try:
            directory = session_filepath.parent
            filename_prefix = f"{session_filepath.name}."
            backups = sorted(
                [f for f in os.listdir(directory) if f.startswith(filename_prefix) and f.endswith(".bak")],
                reverse=True
            )

            for old_backup in backups[self.config.session.backup_count:]:
                backup_path = directory / old_backup
                os.remove(backup_path)
                logger.debug("Old backup removed", extra={"backup_path": str(backup_path)})

        except OSError as e:
            logger.warning("Failed to cleanup old backups", extra={"error": str(e)})

    def save(
        self,
        name: str,
        query_params: Dict[str, Any],
        results: Dict[str, Any],
        compliance_report: Dict[str, Any],
        user: str = "default_user"
    ) -> Path:
        """
        Saves the current analysis state to a named JSON file.

        This method stores various components of an analysis session, including query parameters,
        GIS results, compliance reports, and user metadata, into a uniquely named JSON file
        within the configured session directory. It uses atomic writes to ensure data integrity
        and can create automatic backups.

        Args:
            name: A unique name for this analysis session. This will be used to construct
                  the filename (e.g., "Texas Counties Analysis" -> "Texas Counties Analysis.json").
            query_params: Dictionary of query parameters used for the analysis (e.g., {"where": "STATE_NAME = 'Texas'"}).
            results: Dictionary of results obtained from the GIS query (e.g., feature sets).
            compliance_report: Dictionary containing the generated compliance report data.
            user: Optional identifier for the user saving the session (defaults to "default_user").

        Returns:
            The absolute path to the saved session file.

        Raises:
            ValueError: If the session name is empty or any component (query_params, results, compliance_report)
                        is not a dictionary.
            SessionManagerError: If writing the session file fails due to an OS-level error.
        """
        if not name:
            logger.error("Session name cannot be empty.", extra={"name": name})
            raise ValueError("Session name cannot be empty.")

        # Assign to a temporary instance attribute
        self._temp_session_filepath = None
        try:
            self._temp_session_filepath = self._get_session_path(name)
        except Exception as e:
            logger.error(f"Error getting session path for '{name}': {e}", extra={"name": name, "error": str(e)})
            raise SessionManagerError(f"Failed to determine session path for '{name}': {e}") from e

        logger.info(
            "Saving session",
            extra={
                "session_name": name, # Renamed 'name' to 'session_name'
                "filepath": str(self._temp_session_filepath),
                "user": user,
                "feature_count": len(results.get("features", [])),
            }
        )


        if not isinstance(query_params, dict):
            logger.error("Invalid query_params type", extra={"type": type(query_params)})
            raise ValueError("query_params must be a dictionary.")
        if not isinstance(results, dict):
            logger.error("Invalid results type", extra={"type": type(results)})
            raise ValueError("results must be a dictionary.")
        if not isinstance(compliance_report, dict):
            logger.error("Invalid compliance_report type", extra={"type": type(compliance_report)})
            raise ValueError("compliance_report must be a dictionary.")

        if self.auto_backup:
            self._create_backup(self._temp_session_filepath) # Use instance attribute

        data = {
            "meta": {
                "user": user,
                "timestamp": datetime.now().isoformat(),
                "version": "1.0",
                "session_name": name,
            },
            "query_params": query_params,
            "results": results,
            "report": compliance_report
        }

        try:
            # Ensure the directory for the session file exists
            self._temp_session_filepath.parent.mkdir(parents=True, exist_ok=True)

            tmp_path = self._temp_session_filepath.with_suffix(".json.tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            os.replace(tmp_path, self._temp_session_filepath) # Use instance attribute

            logger.info(
                "Session saved successfully",
                extra={
                    "session_name": name, # Renamed 'name' to 'session_name'
                    "filepath": str(self._temp_session_filepath.resolve()),
                    "size_bytes": self._temp_session_filepath.stat().st_size,
                }
            )

        except OSError as e:
            logger.error(
                "Failed to write session",
                extra={"session_name": name, "filepath": str(self._temp_session_filepath), "error": str(e)} # Renamed 'name' to 'session_name'
            )
            raise SessionManagerError(f"Failed to write session {name} to {self._temp_session_filepath}: {e}") from e

        return self._temp_session_filepath.resolve()

    def load(
        self,
        name: str
    ) -> Dict[str, Any]:
        """
        Loads a specific analysis state from a named JSON file.

        This method retrieves a previously saved analysis session by its unique name
        from the configured session directory.

        Args:
            name: The unique name of the analysis session to load. This corresponds
                  to the 'name' used when the session was saved.

        Returns:
            A dictionary containing the loaded session data, including query parameters,
            GIS results, compliance reports, and metadata.

        Raises:
            ValueError: If the session name is empty.
            FileNotFoundError: If the session file corresponding to the given name does not exist.
            json.JSONDecodeError: If the content of the session file is not valid JSON.
            SessionManagerError: If reading the session file fails due to an OS-level error.
        """
        if not name:
            logger.error("Session name cannot be empty.", extra={"name": name})
            raise ValueError("Session name cannot be empty.")

        session_filepath = self._get_session_path(name)
        logger.info("Loading session", extra={"session_name": name, "filepath": str(session_filepath)}) # Renamed 'name' to 'session_name'

        if not session_filepath.exists():
            logger.error("Session file not found", extra={"name": name, "filepath": str(session_filepath)})
            raise FileNotFoundError(f"Session file for '{name}' not found at {session_filepath}.")

        try:
            with open(session_filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            logger.info(
                "Session loaded successfully",
                extra={
                    "session_name": name, # Renamed 'name' to 'session_name'
                    "filepath": str(session_filepath),
                    "user": data.get("meta", {}).get("user"),
                    "timestamp": data.get("meta", {}).get("timestamp"),
                    "feature_count": len(data.get("results", {}).get("features", [])),
                }
            )

            return data

        except json.JSONDecodeError as e:
            logger.error(
                "Invalid JSON in session file",
                extra={"session_name": name, "filepath": str(session_filepath), "error": str(e)} # Renamed 'name' to 'session_name'
            )
            raise

        except OSError as e:
            logger.error(
                "Failed to read session file",
                extra={"session_name": name, "filepath": str(session_filepath), "error": str(e)} # Renamed 'name' to 'session_name'
            )
            raise SessionManagerError(f"Failed to read session file '{name}' at {session_filepath}: {e}") from e
