from flask import Flask, request, jsonify
from urllib.parse import urlparse, ParseResult
from core import Grok
import time
import threading

app = Flask(__name__)

def format_proxy(proxy: str) -> str:
    # If proxy is empty, None, or just whitespace, return None to indicate no proxy
    if not proxy or (isinstance(proxy, str) and proxy.strip() == ""):
        return None
    
    if not proxy.startswith(("http://", "https://")):
        proxy: str = "http://" + proxy
    
    try:
        parsed: ParseResult = urlparse(proxy)

        if parsed.scheme not in ("http", ""):
            raise ValueError("Not http scheme")

        if not parsed.hostname or not parsed.port:
            raise ValueError("No url and port")

        if parsed.username and parsed.password:
            return f"http://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}"
        
        else:
            return f"http://{parsed.hostname}:{parsed.port}"
    
    except ValueError as e:
        raise ValueError(f"Invalid proxy format: {str(e)}")

def extract_message_from_parts(data):
    """Extract message from the parts format or fallback to message field"""
    message = ""
    
    # Check if the data is in the new format with role and parts
    if 'contents' in data:
        # New format: array of content objects
        for content in data['contents']:
            if isinstance(content, dict) and content.get('role') == 'user':
                parts = content.get('parts', [])
                if isinstance(parts, list):
                    for part in parts:
                        if isinstance(part, dict) and 'text' in part:
                            message += part['text']
    elif 'role' in data and 'parts' in data:
        # Single content object with role and parts
        if data.get('role') == 'user':
            parts = data.get('parts', [])
            if isinstance(parts, list):
                for part in parts:
                    if isinstance(part, dict) and 'text' in part:
                        message += part['text']
    
    # Fallback to old format
    if not message:
        message = data.get('message', '')
    
    return message

@app.route("/ask", methods=["POST"])
def create_conversation():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        proxy = data.get("proxy")
        model = data.get("model", "grok-3-auto")
        extra_data = data.get("extra_data", None)
        
        # Extract message using the new format or fallback to old format
        message = extract_message_from_parts(data)

        if not message:  # Message is required
            return jsonify({"error": "Message is required"}), 400
        
        # Format proxy if provided, otherwise use None
        formatted_proxy = format_proxy(proxy)
        
        # Create Grok instance and call start_convo
        # The Grok class will automatically try to get a free proxy if none is provided
        # and the free-proxy module is available
        grok_instance = Grok(model, formatted_proxy)
        answer = grok_instance.start_convo(message, extra_data)

        return jsonify({
            "status": "success",
            **answer
        })
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "message": "Grok API Server is running"}), 200

if __name__ == "__main__":
    # Enable threading for concurrent requests
    app.run(host="0.0.0.0", port=6969, threaded=True)