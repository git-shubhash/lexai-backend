"""
Legal Document Summarizer - Flask Backend
Main application entry point
"""

import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Application factory"""
    app = Flask(__name__)

    # Configuration
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_FILE_SIZE_MB', 50)) * 1024 * 1024
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
    app.config['SECRET_KEY'] = os.urandom(24)

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Register blueprints
    from routes.upload import upload_bp
    from routes.extract import extract_bp
    from routes.summarize import summarize_bp
    from routes.chat import chat_bp
    from routes.compare import compare_bp
    from routes.export import export_bp

    app.register_blueprint(upload_bp, url_prefix='/api')
    app.register_blueprint(extract_bp, url_prefix='/api')
    app.register_blueprint(summarize_bp, url_prefix='/api')
    app.register_blueprint(chat_bp, url_prefix='/api')
    app.register_blueprint(compare_bp, url_prefix='/api')
    app.register_blueprint(export_bp, url_prefix='/api')

    # Health check
    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({
            'status': 'healthy',
            'message': 'Legal Document Summarizer API is running',
            'model': os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
        })

    # Global error handlers
    @app.errorhandler(413)
    def too_large(e):
        return jsonify({'error': 'File too large. Maximum size is 50MB.'}), 413

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Endpoint not found'}), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Server error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

    logger.info("Legal Document Summarizer API started successfully")
    return app


app = create_app()

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=os.getenv('FLASK_DEBUG', '1') == '1'
    )
