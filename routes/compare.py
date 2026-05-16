"""
Compare route - multi-document comparison
"""

import logging
from flask import Blueprint, request, jsonify
from services.groq_service import compare_documents

logger = logging.getLogger(__name__)
compare_bp = Blueprint('compare', __name__)


@compare_bp.route('/compare', methods=['POST'])
def compare():
    """Compare two legal documents"""
    data = request.get_json(silent=True)

    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    text1 = data.get('text1', '').strip()
    text2 = data.get('text2', '').strip()
    doc1_name = data.get('doc1_name', 'Document 1')
    doc2_name = data.get('doc2_name', 'Document 2')

    if not text1 or not text2:
        return jsonify({'error': 'Both document texts are required'}), 400

    if len(text1) < 50 or len(text2) < 50:
        return jsonify({'error': 'Documents are too short for comparison'}), 400

    try:
        logger.info(f"Comparing: {doc1_name} ({len(text1)} chars) vs {doc2_name} ({len(text2)} chars)")
        result = compare_documents(text1, text2)

        return jsonify({
            'success': True,
            'doc1_name': doc1_name,
            'doc2_name': doc2_name,
            'comparison': result
        })

    except Exception as e:
        logger.error(f"Comparison error: {e}")
        return jsonify({'error': str(e), 'success': False}), 500
