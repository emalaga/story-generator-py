"""
AI Call Logger - Tracks all AI API calls for debugging and monitoring.

This module provides a centralized logging system for all AI calls,
storing details like model, prompt, payload, and response metadata.
Logs are persisted to a JSON file for durability across sessions.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from threading import Lock

# Default log file location
DEFAULT_LOG_FILE = Path(__file__).parent.parent.parent / 'data' / 'ai_logs.json'

# Maximum number of logs to keep
MAX_LOGS = 2000


class AICallLog:
    """Represents a single AI API call log entry."""

    def __init__(
        self,
        call_type: str,
        model: str,
        prompt: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        response_summary: Optional[str] = None,
        reference_images: Optional[List[str]] = None,
        cost: Optional[float] = None,
        duration_ms: Optional[int] = None,
        error: Optional[str] = None,
        project_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        self.id = id or datetime.now().strftime('%Y%m%d%H%M%S%f')
        self.timestamp = timestamp or datetime.now()
        self.call_type = call_type
        self.model = model
        self.prompt = prompt
        self.payload = payload
        self.response_summary = response_summary
        self.reference_images = reference_images or []
        self.cost = cost
        self.duration_ms = duration_ms
        self.error = error
        self.project_id = project_id
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            'call_type': self.call_type,
            'model': self.model,
            'prompt': self.prompt,
            'payload': self.payload,
            'response_summary': self.response_summary,
            'reference_images': self.reference_images,
            'cost': self.cost,
            'duration_ms': self.duration_ms,
            'error': self.error,
            'project_id': self.project_id,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AICallLog':
        """Create an AICallLog from a dictionary."""
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except ValueError:
                timestamp = datetime.now()

        return cls(
            id=data.get('id'),
            timestamp=timestamp,
            call_type=data.get('call_type', 'unknown'),
            model=data.get('model', 'unknown'),
            prompt=data.get('prompt'),
            payload=data.get('payload'),
            response_summary=data.get('response_summary'),
            reference_images=data.get('reference_images'),
            cost=data.get('cost'),
            duration_ms=data.get('duration_ms'),
            error=data.get('error'),
            project_id=data.get('project_id'),
            metadata=data.get('metadata')
        )


class AILogger:
    """
    Singleton logger for tracking AI API calls.

    Thread-safe implementation using a lock for concurrent access.
    Persists logs to a JSON file for durability.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls, log_file: Optional[Path] = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, log_file: Optional[Path] = None):
        if self._initialized:
            return
        self._logs: List[AICallLog] = []
        self._log_lock = Lock()
        self._log_file = log_file or DEFAULT_LOG_FILE
        self._initialized = True
        self._load_from_file()

    def _load_from_file(self):
        """Load logs from the persistent file."""
        try:
            if self._log_file.exists():
                with open(self._log_file, 'r') as f:
                    data = json.load(f)
                    logs_data = data.get('logs', [])
                    self._logs = [AICallLog.from_dict(log_data) for log_data in logs_data]
                    print(f"[AILogger] Loaded {len(self._logs)} logs from {self._log_file}")
        except Exception as e:
            print(f"[AILogger] Error loading logs from file: {e}")
            self._logs = []

    def _save_to_file(self):
        """Save logs to the persistent file."""
        try:
            # Ensure directory exists
            self._log_file.parent.mkdir(parents=True, exist_ok=True)

            # Trim logs if exceeding maximum
            if len(self._logs) > MAX_LOGS:
                self._logs = self._logs[-MAX_LOGS:]

            data = {
                'version': 1,
                'updated_at': datetime.now().isoformat(),
                'logs': [log.to_dict() for log in self._logs]
            }

            with open(self._log_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[AILogger] Error saving logs to file: {e}")

    def log(
        self,
        call_type: str,
        model: str,
        prompt: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        response_summary: Optional[str] = None,
        reference_images: Optional[List[str]] = None,
        cost: Optional[float] = None,
        duration_ms: Optional[int] = None,
        error: Optional[str] = None,
        project_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AICallLog:
        """
        Log an AI API call.

        Args:
            call_type: Type of call (e.g., 'story', 'art_bible', 'page_image')
            model: Model used (e.g., 'gpt-4o', 'gpt-image-1')
            prompt: The prompt sent to the AI
            payload: Full request payload (excluding sensitive data)
            response_summary: Brief summary of the response
            reference_images: List of reference image paths used
            cost: Estimated cost in USD
            duration_ms: Call duration in milliseconds
            error: Error message if call failed
            project_id: Associated project ID
            metadata: Additional metadata

        Returns:
            The created AICallLog entry
        """
        log_entry = AICallLog(
            call_type=call_type,
            model=model,
            prompt=prompt,
            payload=payload,
            response_summary=response_summary,
            reference_images=reference_images,
            cost=cost,
            duration_ms=duration_ms,
            error=error,
            project_id=project_id,
            metadata=metadata
        )

        with self._log_lock:
            self._logs.append(log_entry)
            self._save_to_file()

        return log_entry

    def get_logs(
        self,
        call_type: Optional[str] = None,
        project_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve logs with optional filtering.

        Args:
            call_type: Filter by call type (None for all)
            project_id: Filter by project ID (None for all)
            start_date: Filter by start date (inclusive)
            end_date: Filter by end date (inclusive)
            limit: Maximum number of logs to return
            offset: Number of logs to skip

        Returns:
            List of log dictionaries, newest first
        """
        with self._log_lock:
            # Copy and reverse for newest-first ordering
            logs = list(self._logs)
            logs.reverse()

        # Apply filters
        if call_type and call_type != 'all':
            logs = [log for log in logs if log.call_type == call_type]

        if project_id:
            logs = [log for log in logs if log.project_id == project_id]

        if start_date:
            logs = [log for log in logs if log.timestamp >= start_date]

        if end_date:
            # Include the entire end date (up to 23:59:59)
            end_of_day = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
            logs = [log for log in logs if log.timestamp <= end_of_day]

        # Apply pagination
        logs = logs[offset:offset + limit]

        return [log.to_dict() for log in logs]

    def get_log_count(
        self,
        call_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """Get total count of logs, optionally filtered."""
        with self._log_lock:
            logs = list(self._logs)

        if call_type and call_type != 'all':
            logs = [log for log in logs if log.call_type == call_type]

        if start_date:
            logs = [log for log in logs if log.timestamp >= start_date]

        if end_date:
            end_of_day = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
            logs = [log for log in logs if log.timestamp <= end_of_day]

        return len(logs)

    def delete_logs(self, log_ids: List[str]) -> int:
        """
        Delete specific logs by their IDs.

        Args:
            log_ids: List of log IDs to delete

        Returns:
            Number of logs deleted
        """
        with self._log_lock:
            original_count = len(self._logs)
            self._logs = [log for log in self._logs if log.id not in log_ids]
            deleted_count = original_count - len(self._logs)
            if deleted_count > 0:
                self._save_to_file()
            return deleted_count

    def clear_logs(self):
        """Clear all logs and delete the log file."""
        with self._log_lock:
            self._logs.clear()
            # Delete the file
            if self._log_file.exists():
                try:
                    self._log_file.unlink()
                    print(f"[AILogger] Deleted log file: {self._log_file}")
                except Exception as e:
                    print(f"[AILogger] Error deleting log file: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about logged calls."""
        with self._log_lock:
            logs = list(self._logs)

        if not logs:
            return {
                'total_calls': 0,
                'total_cost': 0.0,
                'calls_by_type': {},
                'error_count': 0
            }

        calls_by_type = {}
        total_cost = 0.0
        error_count = 0

        for log in logs:
            # Count by type
            if log.call_type not in calls_by_type:
                calls_by_type[log.call_type] = 0
            calls_by_type[log.call_type] += 1

            # Sum costs
            if log.cost:
                total_cost += log.cost

            # Count errors
            if log.error:
                error_count += 1

        return {
            'total_calls': len(logs),
            'total_cost': round(total_cost, 4),
            'calls_by_type': calls_by_type,
            'error_count': error_count
        }


# Global singleton instance
ai_logger = AILogger()


def log_ai_call(
    call_type: str,
    model: str,
    prompt: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    response_summary: Optional[str] = None,
    reference_images: Optional[List[str]] = None,
    cost: Optional[float] = None,
    duration_ms: Optional[int] = None,
    error: Optional[str] = None,
    project_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> AICallLog:
    """
    Convenience function to log an AI call using the global logger.

    See AILogger.log() for parameter documentation.
    """
    return ai_logger.log(
        call_type=call_type,
        model=model,
        prompt=prompt,
        payload=payload,
        response_summary=response_summary,
        reference_images=reference_images,
        cost=cost,
        duration_ms=duration_ms,
        error=error,
        project_id=project_id,
        metadata=metadata
    )
