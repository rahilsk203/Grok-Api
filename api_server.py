from flask import Flask, request, jsonify
from urllib.parse import urlparse, ParseResult
from core import Grok
import time
import threading
import re

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
    """Extract message from the parts format including system instructions"""
    full_prompt = ""
    
    # 1. Extract system instructions if present
    system_instr = data.get('system_instruction') or data.get('systemInstruction')
    if system_instr:
        if isinstance(system_instr, dict):
            parts = system_instr.get('parts', [])
            for part in parts:
                if isinstance(part, dict) and 'text' in part:
                    full_prompt += f"System: {part['text']}\n\n"
        elif isinstance(system_instr, str):
            full_prompt += f"System: {system_instr}\n\n"

    # 2. Extract messages from contents
    if 'contents' in data:
        for content in data['contents']:
            role = content.get('role', 'user')
            parts = content.get('parts', [])
            if isinstance(parts, list):
                role_prefix = "System: " if role == 'system' else "User: " if role == 'user' else "Assistant: "
                for part in parts:
                    if isinstance(part, dict) and 'text' in part:
                        full_prompt += f"{role_prefix}{part['text']}\n\n"
    
    # 3. Fallback to old format if nothing extracted yet
    if not full_prompt:
        message = data.get('message', '')
        if message:
            full_prompt = message
    
    return full_prompt.strip()

def clean_response(text):
    """Clean Grok's response to ensure it only contains [think] and [answer] tags"""
    if not text:
        return text
        
    # Find the first [think] and the last [/answer]
    think_start = text.find("[think]")
    answer_end = text.rfind("[/answer]")
    
    if think_start != -1 and answer_end != -1:
        # Extract everything between the first tag and last tag
        cleaned = text[think_start:answer_end + len("[/answer]")]
        return cleaned
    
    # Fallback: if tags are missing or malformed, try to keep it as is 
    # but strip common conversational prefixes
    prefixes_to_strip = [
        "Certainly!", "Here is the reasoning:", "Based on the screen,", 
        "I've analyzed the state.", "Sure,", "Okay,"
    ]
    
    cleaned = text.strip()
    for prefix in prefixes_to_strip:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
            
    return cleaned

@app.route("/ask", methods=["POST"])
def create_conversation():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        proxy = data.get("proxy")
        model = data.get("model", "grok-3-auto")
        extra_data = data.get("extra_data", None)
        
        # Extract full prompt including system instructions
        message = extract_message_from_parts(data)

        if not message:  # Message is required
            return jsonify({"error": "Message is required"}), 400
        
        # Format proxy if provided, otherwise use None
        formatted_proxy = format_proxy(proxy)
        
        # Create Grok instance and call start_convo
        grok_instance = Grok(model, formatted_proxy)
        answer = grok_instance.start_convo(message, extra_data)

        # Clean the response text
        if "response" in answer:
            answer["response"] = clean_response(answer["response"])
            
        if "stream_response" in answer and isinstance(answer["stream_response"], list):
            # For stream response, we might need more complex logic if we want to clean it real-time,
            # but for now we'll just clean the final combined response if it's available.
            pass

        return jsonify({
            "status": "success",
            **answer
        })
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "message": "Grok API Server is running"}), 200

@app.route("/v1/chat/completions", methods=["POST"])
def openai_compatible():
    """OpenAI compatible endpoint that routes to /ask logic"""
    return create_conversation()

if __name__ == "__main__":
    # Enable threading for concurrent requests
    app.run(host="0.0.0.0", port=6969, threaded=True)