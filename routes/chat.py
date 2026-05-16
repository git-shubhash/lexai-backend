"""
Chat route - AI legal assistant for document Q&A
"""

import logging
from flask import Blueprint, request, jsonify, Response, stream_with_context
from services.groq_service import chat_with_document, client, MODEL

logger = logging.getLogger(__name__)
chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/chat', methods=['POST'])
def chat():
    """AI chat about uploaded legal document"""
    data = request.get_json(silent=True)

    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    text = data.get('text', '')
    question = data.get('question', '').strip()
    history = data.get('history', [])

    if not text:
        return jsonify({'error': 'Document text is required'}), 400

    if not question:
        return jsonify({'error': 'Question is required'}), 400

    try:
        logger.info(f"Chat question: {question[:100]}")
        answer = chat_with_document(text, question, history)

        return jsonify({
            'success': True,
            'question': question,
            'answer': answer,
            'model': MODEL
        })

    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@chat_bp.route('/chat/stream', methods=['POST'])
def chat_stream():
    """Streaming AI chat response"""
    data = request.get_json(silent=True)

    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    text = data.get('text', '')
    question = data.get('question', '').strip()
    history = data.get('history', [])

    if not text or not question:
        return jsonify({'error': 'text and question are required'}), 400

    def generate():
        try:
            messages = [
                {"role": "system", "content": f"""You are an expert legal document analyst.
Answer questions about this legal document precisely and clearly.

DOCUMENT:
{text[:8000]}"""}
            ]

            for msg in history[-6:]:
                messages.append({"role": msg["role"], "content": msg["content"]})

            messages.append({"role": "user", "content": question})

            stream = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.4,
                max_tokens=2048,
                stream=True
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield f"data: {content}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            yield f"data: ERROR: {str(e)}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )
