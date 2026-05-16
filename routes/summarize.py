"""
Summarize route - AI-powered legal document analysis
"""

import logging
from flask import Blueprint, request, jsonify
from services.groq_service import summarize_document
from services.extraction_service import extract_text

logger = logging.getLogger(__name__)
summarize_bp = Blueprint('summarize', __name__)


@summarize_bp.route('/summarize', methods=['POST'])
def summarize():
    """Generate AI summary of legal document"""
    data = request.get_json(silent=True)

    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    text = data.get('text', '')

    if not text or not text.strip():
        return jsonify({'error': 'Document text is required'}), 400

    if len(text) < 50:
        return jsonify({'error': 'Document text is too short for analysis'}), 400

    try:
        logger.info(f"Starting summarization for {len(text)} chars")
        result = summarize_document(text)

        # Add metadata
        result['text_length'] = len(text)
        result['word_count'] = len(text.split())

        return jsonify({
            'success': True,
            'summary': result
        })

    except Exception as e:
        logger.error(f"Summarization error: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@summarize_bp.route('/analyze', methods=['POST'])
def analyze():
    """Upload file and immediately analyze (combined endpoint)"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    file_bytes = file.read()

    # Extract text
    extraction = extract_text(file_bytes, file.filename)
    if not extraction['success'] or extraction['is_empty']:
        return jsonify({'error': 'Could not extract text from document', 'extraction': extraction}), 422

    # Summarize
    try:
        summary = summarize_document(extraction['text'])
        return jsonify({
            'success': True,
            'filename': file.filename,
            'extraction': {
                'method': extraction['method'],
                'word_count': extraction['word_count'],
                'char_count': extraction['char_count']
            },
            'summary': summary
        })
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return jsonify({'error': str(e)}), 500
