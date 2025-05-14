from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "llama2")

@app.route('/health', methods=['GET'])
def health_check():
    try:
        # Check if Ollama server is accessible
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        ollama_healthy = response.status_code == 200
        
        return jsonify({
            "status": "healthy",
            "ollama_connection": ollama_healthy,
            "available_models": response.json() if ollama_healthy else None
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

@app.route('/generate', methods=['POST'])
def generate_response():
    data = request.json
    
    if not data or 'prompt' not in data:
        return jsonify({"error": "Missing prompt in request"}), 400
    
    model = data.get('model', DEFAULT_MODEL)
    prompt = data['prompt']
    system_prompt = data.get('system_prompt', "You are a helpful voice assistant.")
    
    try:
        # Call Ollama API
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code != 200:
            return jsonify({"error": f"Ollama API error: {response.text}"}), response.status_code
        
        result = response.json()
        return jsonify({
            "response": result.get("response", ""),
            "model": model,
            "total_duration": result.get("total_duration", 0)
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8002)