"""
Logs Routes for REST API.

Handles endpoints for retrieving and managing AI call logs.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify

from src.utils.ai_logger import ai_logger

# Create blueprint
logs_bp = Blueprint('logs', __name__)


def parse_date(date_str: str) -> datetime:
    """Parse a date string in YYYY-MM-DD format."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None


@logs_bp.route('', methods=['GET'])
def get_logs():
    """
    GET /api/logs - Retrieve AI call logs

    Query parameters:
        type: Filter by call type (optional)
        project_id: Filter by project ID (optional)
        start_date: Filter by start date in YYYY-MM-DD format (optional)
        end_date: Filter by end date in YYYY-MM-DD format (optional)
        limit: Maximum number of logs to return (default: 100, max: 500)
        offset: Number of logs to skip (default: 0)

    Returns:
        200: List of log entries with metadata
    """
    try:
        call_type = request.args.get('type', None)
        project_id = request.args.get('project_id', None)
        start_date = parse_date(request.args.get('start_date', None))
        end_date = parse_date(request.args.get('end_date', None))
        limit = min(int(request.args.get('limit', 100)), 500)
        offset = int(request.args.get('offset', 0))

        logs = ai_logger.get_logs(
            call_type=call_type,
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )

        total_count = ai_logger.get_log_count(
            call_type=call_type,
            start_date=start_date,
            end_date=end_date
        )

        return jsonify({
            'logs': logs,
            'total': total_count,
            'limit': limit,
            'offset': offset
        }), 200

    except Exception as e:
        return jsonify({'error': f'Failed to retrieve logs: {str(e)}'}), 500


@logs_bp.route('/stats', methods=['GET'])
def get_stats():
    """
    GET /api/logs/stats - Get statistics about AI calls

    Returns:
        200: Statistics including total calls, costs, and breakdown by type
    """
    try:
        stats = ai_logger.get_stats()
        return jsonify(stats), 200

    except Exception as e:
        return jsonify({'error': f'Failed to retrieve stats: {str(e)}'}), 500


@logs_bp.route('/delete', methods=['POST'])
def delete_logs():
    """
    POST /api/logs/delete - Delete specific log entries

    Request body:
    {
        "log_ids": list[str] (required) - List of log IDs to delete
    }

    Returns:
        200: Logs deleted successfully with count
        400: Invalid request
        500: Server error
    """
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400

        data = request.get_json()
        log_ids = data.get('log_ids', [])

        if not log_ids or not isinstance(log_ids, list):
            return jsonify({'error': 'log_ids must be a non-empty list'}), 400

        deleted_count = ai_logger.delete_logs(log_ids)

        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Deleted {deleted_count} log(s)'
        }), 200

    except Exception as e:
        return jsonify({'error': f'Failed to delete logs: {str(e)}'}), 500


@logs_bp.route('/clear', methods=['POST'])
def clear_logs():
    """
    POST /api/logs/clear - Clear all logs and delete the log file

    Returns:
        200: Logs cleared successfully
    """
    try:
        ai_logger.clear_logs()
        return jsonify({'success': True, 'message': 'All logs cleared and log file deleted'}), 200

    except Exception as e:
        return jsonify({'error': f'Failed to clear logs: {str(e)}'}), 500
