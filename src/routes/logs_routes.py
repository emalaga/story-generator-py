"""
Logs Routes for REST API.

Handles endpoints for retrieving AI call logs.
"""

from flask import Blueprint, request, jsonify

from src.utils.ai_logger import ai_logger

# Create blueprint
logs_bp = Blueprint('logs', __name__)


@logs_bp.route('', methods=['GET'])
def get_logs():
    """
    GET /api/logs - Retrieve AI call logs

    Query parameters:
        type: Filter by call type (optional)
        project_id: Filter by project ID (optional)
        limit: Maximum number of logs to return (default: 100, max: 500)
        offset: Number of logs to skip (default: 0)

    Returns:
        200: List of log entries with metadata
    """
    try:
        call_type = request.args.get('type', None)
        project_id = request.args.get('project_id', None)
        limit = min(int(request.args.get('limit', 100)), 500)
        offset = int(request.args.get('offset', 0))

        logs = ai_logger.get_logs(
            call_type=call_type,
            project_id=project_id,
            limit=limit,
            offset=offset
        )

        total_count = ai_logger.get_log_count(call_type)

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


@logs_bp.route('/clear', methods=['POST'])
def clear_logs():
    """
    POST /api/logs/clear - Clear all logs

    Returns:
        200: Logs cleared successfully
    """
    try:
        ai_logger.clear_logs()
        return jsonify({'success': True, 'message': 'Logs cleared'}), 200

    except Exception as e:
        return jsonify({'error': f'Failed to clear logs: {str(e)}'}), 500
