"""
Extract route - text extraction from uploaded documents
"""

import os
import logging
from flask import Blueprint, request, jsonify, current_app
from services.extraction_service import extract_text

logger = logging.getLogger(__name__)
extract_bp = Blueprint('extract', __name__)


@extract_bp.route('/extract', methods=['POST'])
def extract():
    """Extract text from uploaded file by file_id or direct upload"""
    data = request.get_json(silent=True)

    if data and 'file_id' in data:
        # Extract from previously uploaded file
        file_id = data['file_id']
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')

        # Find the file
        target_file = None
        for fname in os.listdir(upload_folder):
            if fname.startswith(file_id):
                target_file = os.path.join(upload_folder, fname)
                break

        if not target_file or not os.path.exists(target_file):
            return jsonify({'error': 'File not found. Please upload again.'}), 404

        try:
            with open(target_file, 'rb') as f:
                file_bytes = f.read()

            filename = os.path.basename(target_file)
            result = extract_text(file_bytes, filename)

            logger.info(f"Extracted text from {file_id}: {result.get('char_count', 0)} chars")
            return jsonify(result)

        except Exception as e:
            logger.error(f"Extraction error: {e}")
            return jsonify({'error': str(e), 'success': False}), 500

    elif 'file' in request.files:
        # Direct file upload + extract
        file = request.files['file']
        file_bytes = file.read()
        result = extract_text(file_bytes, file.filename)
        return jsonify(result)

    else:
        return jsonify({'error': 'Provide file_id or upload a file'}), 400
