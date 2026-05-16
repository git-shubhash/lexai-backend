"""
Upload route - handles file upload and validation
"""

import os
import uuid
import logging
from flask import Blueprint, request, jsonify, current_app

logger = logging.getLogger(__name__)
upload_bp = Blueprint('upload', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'png', 'jpg', 'jpeg', 'tiff', 'bmp', 'gif'}


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@upload_bp.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload - stores temporarily in memory"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({
            'error': f'File type not supported. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400

    try:
        file_bytes = file.read()
        file_size = len(file_bytes)
        max_size = current_app.config.get('MAX_CONTENT_LENGTH', 50 * 1024 * 1024)

        if file_size > max_size:
            return jsonify({'error': f'File too large. Max size: {max_size // (1024*1024)}MB'}), 413

        # Generate unique file ID
        file_id = str(uuid.uuid4())
        extension = file.filename.rsplit('.', 1)[1].lower()

        # Save temporarily to uploads folder
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        temp_path = os.path.join(upload_folder, f"{file_id}.{extension}")

        with open(temp_path, 'wb') as f:
            f.write(file_bytes)

        logger.info(f"File uploaded: {file.filename} -> {file_id} ({file_size} bytes)")

        return jsonify({
            'success': True,
            'file_id': file_id,
            'filename': file.filename,
            'file_size': file_size,
            'file_size_mb': round(file_size / (1024 * 1024), 2),
            'extension': extension,
            'temp_path': temp_path
        })

    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': str(e)}), 500


@upload_bp.route('/upload/multiple', methods=['POST'])
def upload_multiple():
    """Handle multiple file uploads"""
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400

    files = request.files.getlist('files')
    results = []

    for file in files:
        if file.filename == '' or not allowed_file(file.filename):
            continue

        try:
            file_bytes = file.read()
            file_id = str(uuid.uuid4())
            extension = file.filename.rsplit('.', 1)[1].lower()

            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            temp_path = os.path.join(upload_folder, f"{file_id}.{extension}")

            with open(temp_path, 'wb') as f:
                f.write(file_bytes)

            results.append({
                'file_id': file_id,
                'filename': file.filename,
                'file_size': len(file_bytes),
                'extension': extension,
                'temp_path': temp_path
            })
        except Exception as e:
            results.append({'filename': file.filename, 'error': str(e)})

    return jsonify({'success': True, 'files': results})
