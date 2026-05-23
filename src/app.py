import json
from flask import Flask, request, jsonify, render_template, Response, stream_with_context

# Support both local execution (from src/) and Vercel serverless (from project root)
try:
    from commands import process_command
    from ai import aiprocess, aiprocess_stream
    from database import (
        save_conversation,
        get_conversations,
        create_session,
        get_sessions,
        update_session_title,
        delete_session,
        clear_conversations,
    )
except ImportError:
    from src.commands import process_command
    from src.ai import aiprocess, aiprocess_stream
    from src.database import (
        save_conversation,
        get_conversations,
        create_session,
        get_sessions,
        update_session_title,
        delete_session,
        clear_conversations,
    )

app = Flask(__name__, template_folder='../templates', static_folder='../static')


# ── Pages ────────────────────────────────────────────────────────────

@app.route('/')
def home():
    return render_template('index.html')


# ── Command API ──────────────────────────────────────────────────────

@app.route('/api/command', methods=['POST'])
def command():
    """Process a command and return the response."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON body'}), 400

        command_text = data.get('command', '').strip()
        session_id = data.get('session_id')

        if not command_text:
            return jsonify({'error': 'No command provided'}), 400

        # Get conversation history for context
        history = get_conversations(session_id, limit=10) if session_id else []

        response_text = process_command(command_text, history)
        if response_text is None:
            response_text = aiprocess(command_text, history)
            
        save_conversation(command_text, response_text, session_id)

        return jsonify({'response': response_text})

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/stream', methods=['POST'])
def stream():
    """Stream AI response via Server-Sent Events."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON body'}), 400

        command_text = data.get('command', '').strip()
        session_id = data.get('session_id')

        if not command_text:
            return jsonify({'error': 'No command provided'}), 400

        history = get_conversations(session_id, limit=10) if session_id else []

        def generate():
            # Check local commands first
            local_response = process_command(command_text, history)
            
            if local_response is not None:
                # Instantly stream the local response
                yield f"data: {json.dumps({'chunk': local_response})}\n\n"
                save_conversation(command_text, local_response, session_id)
                yield f"data: {json.dumps({'done': True, 'full_response': local_response})}\n\n"
                return

            # Otherwise, use AI stream
            full_response = []
            for chunk in aiprocess_stream(command_text, history):
                full_response.append(chunk)
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"

            # Save the complete response
            complete = "".join(full_response)
            save_conversation(command_text, complete, session_id)
            yield f"data: {json.dumps({'done': True, 'full_response': complete})}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
            }
        )

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


# ── Session API ──────────────────────────────────────────────────────

@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    """List all conversation sessions."""
    try:
        sessions = get_sessions()
        return jsonify({'sessions': sessions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions', methods=['POST'])
def new_session():
    """Create a new conversation session."""
    try:
        data = request.get_json() or {}
        title = data.get('title', 'New Chat')
        session_id = create_session(title)
        return jsonify({'session_id': session_id, 'title': title})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions/<session_id>', methods=['PUT'])
def rename_session(session_id):
    """Rename a conversation session."""
    try:
        data = request.get_json()
        if not data or 'title' not in data:
            return jsonify({'error': 'Title is required'}), 400
        update_session_title(session_id, data['title'])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def remove_session(session_id):
    """Delete a conversation session and its history."""
    try:
        delete_session(session_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── History API ──────────────────────────────────────────────────────

@app.route('/api/history', methods=['GET'])
def get_history():
    """Retrieve conversation history for a session."""
    try:
        session_id = request.args.get('session_id')
        limit = int(request.args.get('limit', 50))
        conversations = get_conversations(session_id, limit)
        return jsonify({'conversations': conversations})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/history', methods=['DELETE'])
def delete_history():
    """Clear conversation history."""
    try:
        session_id = request.args.get('session_id')
        clear_conversations(session_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Keep the old /command endpoint for backward compatibility
@app.route('/command', methods=['POST'])
def command_legacy():
    """Legacy endpoint — redirects to /api/command."""
    return command()
