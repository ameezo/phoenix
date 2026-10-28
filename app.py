import os
import re
from datetime import datetime
from io import BytesIO
from flask import Flask, request, send_from_directory, send_file, render_template, jsonify, abort
from werkzeug.utils import secure_filename

app = Flask(__name__)

BASE_DIR = os.path.abspath("project_phoenix")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded")

os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# File extensions where the server IP should be dynamically updated on download
TEXT_EXTENSIONS = {".txt", ".ps1", ".bat", ".cmd", ".sh", ".py", ".md", ".json", ".xml"}

def get_files_only(directory):
    """Returns a sorted list of visible files, ignoring subdirectories and hidden files."""
    return sorted([
        f for f in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, f)) and not f.startswith(".")
    ])

@app.route("/", methods=["GET"])
def index():
    files = get_files_only(BASE_DIR)
    return render_template(
        "index.html",
        title="Project Files",
        page="main",
        banner="Hey, complete your project by downloading these files.",
        current_path="project_phoenix/",
        files=files,
        allow_download=True
    )

@app.route("/download/<path:filename>", methods=["GET"])
def download_file(filename):
    file_path = os.path.join(BASE_DIR, filename)
    if not os.path.isfile(file_path) or filename.startswith("."):
        abort(404)

    _, ext = os.path.splitext(filename)
    
    # Dynamically rewrite the IP:Port in script/text files before sending to the client
    if ext.lower() in TEXT_EXTENSIONS:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # request.host automatically holds the <SERVER_IP>:<PORT> the PC used (e.g. 192.168.1.67:5001)
            server_host = request.host

            # 1. Replace {{SERVER_IP}} placeholder if used in the file
            content = content.replace("{{SERVER_IP}}", server_host)

            # 2. Also replace any hardcoded http://<IP>:<PORT> automatically
            content = re.sub(
                r"http://(?:\d{1,3}\.){3}\d{1,3}:\d+",
                f"http://{server_host}",
                content
            )

            buffer = BytesIO(content.encode("utf-8"))
            return send_file(
                buffer,
                as_attachment=True,
                download_name=filename,
                mimetype="application/octet-stream"
            )
        except UnicodeDecodeError:
            # If the file isn't valid UTF-8 text, fall back to normal binary download
            pass

    return send_from_directory(BASE_DIR, filename, as_attachment=True)

@app.route("/uploaded", methods=["GET"])
def view_uploaded():
    files = get_files_only(UPLOAD_DIR)
    return render_template(
        "index.html",
        title="Uploaded Files",
        page="uploaded",
        banner=None,
        current_path="project_phoenix/uploaded/",
        files=files,
        allow_download=False
    )

# Supports both /uploaded and /uploaded/<filename>
@app.route("/upload", methods=["POST"])
@app.route("/uploaded", methods=["POST"])
@app.route("/uploaded/<path:custom_name>", methods=["POST"])
def handle_upload(custom_name=None):
    content_type = request.content_type or ""

    # Case 1: Standard multipart/form-data upload (e.g., curl -F "file=@...")
    if "multipart/form-data" in content_type and "file" in request.files:
        uploaded_file = request.files["file"]
        if uploaded_file.filename == "":
            return jsonify({"error": "Empty filename."}), 400

        filename = secure_filename(custom_name or uploaded_file.filename)
        save_path = os.path.join(UPLOAD_DIR, filename)
        uploaded_file.save(save_path)

        return jsonify({
            "status": "success",
            "message": f"File '{filename}' uploaded to project_phoenix/uploaded/"
        }), 201

    # Case 2: Raw body upload from PowerShell Invoke-WebRequest -InFile
    # parse_form_data=False prevents Flask from consuming/corrupting binary streams
    raw_data = request.get_data(cache=False, parse_form_data=False)

    if raw_data is not None and (len(raw_data) > 0 or request.content_length == 0):
        # Auto-detect if the uploaded binary is a ZIP archive (starts with 'PK')
        default_name = "phoenix_staging.zip" if raw_data.startswith(b"PK") else "newfile.txt"

        raw_filename = (
            custom_name
            or request.args.get("name")
            or request.headers.get("X-Filename")
            or default_name
        )
        filename = secure_filename(raw_filename)
        save_path = os.path.join(UPLOAD_DIR, filename)

        with open(save_path, "wb") as f:
            f.write(raw_data)

        return jsonify({
            "status": "success",
            "message": f"Raw file saved as '{filename}' ({len(raw_data)} bytes) in project_phoenix/uploaded/"
        }), 201

    return jsonify({"error": "No file data received."}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
