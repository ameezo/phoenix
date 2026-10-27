import os
from flask import Flask, request, send_from_directory, render_template, jsonify, abort
from werkzeug.utils import secure_filename

app = Flask(__name__)

BASE_DIR = os.path.abspath("project_phoenix")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded")

os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

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

@app.route("/upload", methods=["POST"])
@app.route("/uploaded", methods=["POST"])
def handle_upload():
    if "file" not in request.files:
        return jsonify({"error": "No 'file' field provided in the request."}), 400
    
    uploaded_file = request.files["file"]
    if uploaded_file.filename == "":
        return jsonify({"error": "Empty filename."}), 400

    filename = secure_filename(uploaded_file.filename)
    save_path = os.path.join(UPLOAD_DIR, filename)
    uploaded_file.save(save_path)

    return jsonify({
        "status": "success",
        "message": f"File '{filename}' uploaded to project_phoenix/uploaded/"
    }), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
