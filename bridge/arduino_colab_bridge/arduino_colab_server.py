"""
remote_server.py

A simple HTTP server for the Arduino Colab Kernel RemoteBackend.
- Accepts requests from the RemoteBackend client (with token authentication).
- Uses LocalBackend and SerialPort to communicate with local hardware.
- Accepts zipped project directories, unpacks them, and uses them as sketch sources.

Usage:
    python remote_server.py
    python remote_server.py --port 5000 --token YOUR_TOKEN

API:
    POST /compile
    POST /upload
    POST /serial/open
    POST /serial/close
    POST /serial/read
    POST /serial/readlines
    POST /serial/write
"""

import os
import io
import zipfile
import base64
import shutil
import argparse
import secrets
import socket
from functools import wraps
from flask import Flask, request, jsonify, abort, render_template_string

from arduino_colab_kernel.backends.local_backend import LocalBackend
from arduino_colab_kernel.project.config import DEFAULT_REMOTE_URL
from arduino_colab_kernel.board.board import Board

DEFULT_PROJECT_DIR = "project_workspace"

def parse_host_and_port(remote_url) -> tuple[str, int]:
    """Parse port and URL from remote_url."""
    if remote_url.startswith("http://"):
        remote_url = remote_url[len("http://") :]
    elif remote_url.startswith("https://"):
        remote_url = remote_url[len("https://") :]
    if "/" in remote_url:
        remote_url = remote_url.split("/")[0]
    if ":" in remote_url:
        host, port_str = remote_url.split(":")
        try:
            port = int(port_str)
        except ValueError:
            port = 5000
    else:
        host = remote_url
        port = 5000
    return host, port

def find_free_port(default_port=5000):
    """Find a free port, starting from default_port."""
    port = default_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                port += 1

# Parse default host and port from DEFAULT_REMOTE_URL
HOSTNAME, PORT = parse_host_and_port(DEFAULT_REMOTE_URL)

# --- Configurable token and port ---
parser = argparse.ArgumentParser(description="Arduino Colab Kernel Remote Server")
parser.add_argument("--port", type=int, help="Port to run the server on")
parser.add_argument("--token", type=str, help="API token for authentication")
args = parser.parse_args()

if args.port:
    PORT = args.port
else:
    # Check if the default port is free, otherwise find a free one
    PORT = find_free_port(5000)

if args.token:
    API_TOKEN = args.token
else:
    API_TOKEN = secrets.token_urlsafe(24)
    

app = Flask(__name__)
backend = LocalBackend()

def require_token(func):
    @wraps(func)
    def wrapper(*a, **kw):
        token = request.headers.get("X-Auth-Token")
        if token != API_TOKEN:
            abort(401, description="Invalid or missing API token.")
        return func(*a, **kw)
    return wrapper

def extract_sketch_dir(payload):
    """
    Extracts a sketch directory from the payload.
    Supports zipped directories (sketch_zip_b64) or single .ino files (sketch_b64).
    Returns the path to the extracted directory or file.
    Uses a local relative directory 'project_workspace' (rewritten every time).
    """
    if "sketch_name" in payload:
        sketch_name = payload["sketch_name"]
    else:
        sketch_name = "sketch"
        print("Warning: No sketch_name provided, using default 'sketch'.")
    
    # Remove previous contents if exist
    if os.path.exists(DEFULT_PROJECT_DIR):
        shutil.rmtree(DEFULT_PROJECT_DIR)
    # Create workspace directory
    workspace_dir = os.path.abspath(os.path.join(DEFULT_PROJECT_DIR, sketch_name))
    os.makedirs(workspace_dir, exist_ok=True)

    if "sketch_zip_b64" in payload:
        zipped = base64.b64decode(payload["sketch_zip_b64"])
        with zipfile.ZipFile(io.BytesIO(zipped), "r") as zf:
            zf.extractall(workspace_dir)
        return workspace_dir
    elif "sketch_b64" in payload:
        ino_bytes = base64.b64decode(payload["sketch_b64"])
        ino_path = os.path.join(workspace_dir, "sketch.ino")
        with open(ino_path, "wb") as f:
            f.write(ino_bytes)
        return workspace_dir
    else:
        raise ValueError("No sketch data found in payload.")

def cleanup_dir(path):
    """No-op: workspace is always rewritten, so no cleanup needed."""

def get_board_from_payload(payload):
    """Deserialize board from payload."""
    board_data = payload.get("board")
    if not board_data:
        raise ValueError("Missing board data in payload.")
    # Board expects name, fqbn, port, serial config
    name = board_data.get("name")
    fqbn = board_data.get("fqbn")
    port = board_data.get("port")
    serial_cfg = board_data.get("serial", {})
    board = Board(name=name, fqbn=fqbn, port=port)
    board.serial.configure(**serial_cfg)
    return board

@app.route("/compile", methods=["POST"])
@require_token
def compile_sketch():
    """
    Compiles the provided sketch directory for the given board.
    Expects: board, sketch_zip_b64 or sketch_b64, extra_args
    """
    payload = request.get_json(force=True)
    sketch_dir = extract_sketch_dir(payload)
    try:
        board = get_board_from_payload(payload)
        extra_args = payload.get("extra_args", [])
        result = backend.compile(board, sketch_dir, extra_args)
        return jsonify(result)
    finally:
        cleanup_dir(sketch_dir)

@app.route("/upload", methods=["POST"])
@require_token
def upload_sketch():
    """
    Uploads the provided sketch directory to the board.
    Expects: board, sketch_zip_b64 or sketch_b64, extra_args
    """
    payload = request.get_json(force=True)
    sketch_dir = extract_sketch_dir(payload)
    try:
        board = get_board_from_payload(payload)
        extra_args = payload.get("extra_args", [])
        result = backend.upload(board, sketch_dir, extra_args)
        return jsonify(result)
    finally:
        cleanup_dir(sketch_dir)

@app.route("/serial/open", methods=["POST"])
@require_token
def serial_open():
    """
    Opens the serial port for the board.
    Expects: board
    """
    payload = request.get_json(force=True)
    board = get_board_from_payload(payload)
    backend.open_serial(board)
    return jsonify({"status": "ok"})

@app.route("/serial/close", methods=["POST"])
@require_token
def serial_close():
    """
    Closes the serial port for the board.
    Expects: board
    """
    payload = request.get_json(force=True)
    board = get_board_from_payload(payload)
    backend.close_serial(board)
    return jsonify({"status": "ok"})

@app.route("/serial/read", methods=["POST"])
@require_token
def serial_read():
    """
    Reads bytes from the serial port.
    Expects: board, size
    """
    payload = request.get_json(force=True)
    board = get_board_from_payload(payload)
    size = int(payload.get("size", -1))
    backend.open_serial(board)
    try:
        data = backend.read_serial(board, size)
        return jsonify({"data_b64": base64.b64encode(data).decode("ascii")})
    finally:
        backend.close_serial(board)

@app.route("/serial/readlines", methods=["POST"])
@require_token
def serial_readlines():
    """
    Reads lines from the serial port.
    Expects: board, size
    """
    payload = request.get_json(force=True)
    board = get_board_from_payload(payload)
    size = int(payload.get("size", 1))
    backend.open_serial(board)
    try:
        lines = backend.readlines_serial(board, size)
        return jsonify({"lines": lines})
    finally:
        backend.close_serial(board)

@app.route("/serial/write", methods=["POST"])
@require_token
def serial_write():
    """
    Writes data to the serial port.
    Expects: board, data_b64, append_newline
    """
    payload = request.get_json(force=True)
    board = get_board_from_payload(payload)
    data_b64 = payload.get("data_b64")
    append_newline = bool(payload.get("append_newline", True))
    if not data_b64:
        return jsonify({"written": 0})
    data = base64.b64decode(data_b64)
    backend.open_serial(board)
    try:
        written = backend.write_serial(board, data, append_newline)
        return jsonify({"written": written})
    finally:
        backend.close_serial(board)

INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Arduino Colab Kernel Remote Server</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 2em; }
        .copy-field { display: flex; align-items: center; margin-bottom: 1em; }
        input[type=text] { width: 400px; padding: 0.5em; font-size: 1em; }
        button { margin-left: 0.5em; padding: 0.5em 1em; font-size: 1em; cursor: pointer; }
        .label { min-width: 120px; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Arduino Colab Kernel Remote Server</h1>
    <div class="copy-field">
        <span class="label">Server URL:</span>
        <input type="text" id="url" value="{{ url }}" readonly>
        <button onclick="copyToClipboard('url')">Copy</button>
    </div>
    <div class="copy-field">
        <span class="label">API Token:</span>
        <input type="text" id="token" value="{{ token }}" readonly>
        <button onclick="copyToClipboard('token')">Copy</button>
    </div>
    <script>
        function copyToClipboard(elementId) {
            var copyText = document.getElementById(elementId);
            copyText.select();
            copyText.setSelectionRange(0, 99999); // For mobile devices
            document.execCommand("copy");
        }
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    url = f"http://{HOSTNAME}:{PORT}/"
    return render_template_string(INDEX_HTML, url=url, token=API_TOKEN)

if __name__ == "__main__":
    url = f"http://{HOSTNAME}:{PORT}/"
    print(f"Arduino Colab Kernel Remote Server running on port {PORT}")
    print(f"API URL: {url}")
    print(f"API token: {API_TOKEN}")
    app.run(host=HOSTNAME, port=PORT)