"""
AI Call Logger - Tracks all AI API calls for debugging and monitoring.

This module provides a centralized logging system for all AI calls,
storing details like model, prompt, payload, and response metadata.
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from threading import Lock
from collections import deque

# Maximum number of logs to keep in memory
MAX_LOGS = 500


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
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = datetime.now().strftime('%Y%m%d%H%M%S%f')
        self.timestamp = datetime.now()
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
            'timestamp': self.timestamp.isoformat(),
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


class AILogger:
    """
    Singleton logger for tracking AI API calls.

    Thread-safe implementation using a lock for concurrent access.
    Maintains a fixed-size buffer of recent logs.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._logs: deque = deque(maxlen=MAX_LOGS)
        self._log_lock = Lock()
        self._initialized = True

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

        return log_entry

    def get_logs(
        self,
        call_type: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve logs with optional filtering.

        Args:
            call_type: Filter by call type (None for all)
            project_id: Filter by project ID (None for all)
            limit: Maximum number of logs to return
            offset: Number of logs to skip

        Returns:
            List of log dictionaries, newest first
        """
        with self._log_lock:
            # Convert to list and reverse for newest-first ordering
            logs = list(self._logs)
            logs.reverse()

        # Apply filters
        if call_type and call_type != 'all':
            logs = [log for log in logs if log.call_type == call_type]

        if project_id:
            logs = [log for log in logs if log.project_id == project_id]

        # Apply pagination
        logs = logs[offset:offset + limit]

        return [log.to_dict() for log in logs]

    def get_log_count(self, call_type: Optional[str] = None) -> int:
        """Get total count of logs, optionally filtered by type."""
        with self._log_lock:
            if call_type and call_type != 'all':
                return sum(1 for log in self._logs if log.call_type == call_type)
            return len(self._logs)

    def clear_logs(self):
        """Clear all logs."""
        with self._log_lock:
            self._logs.clear()

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
