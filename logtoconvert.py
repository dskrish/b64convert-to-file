
import json
import base64
from pathlib import Path

# Load the JSON file
with open("input.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Get the list of attachments
archivos = data["Archivos"]

if not isinstance(archivos, list) or not archivos:
    raise ValueError("Archivos is empty or is not a list.")

for i, archivo in enumerate(archivos, start=1):
    b64 = archivo["ArchivoBase64"]

    # Remove data URI prefix if present
    if b64.startswith("data:"):
        b64 = b64.split(",", 1)[1]

    # Decode Base64
    raw = base64.b64decode(b64, validate=True)

    # Detect file type
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        ext = "png"
    elif raw.startswith(b"\xff\xd8\xff"):
        ext = "jpg"
    elif raw.startswith((b"GIF87a", b"GIF89a")):
        ext = "gif"
    elif raw.startswith(b"RIFF") and raw[8:12] == b"WEBP":
        ext = "webp"
    elif raw.startswith(b"%PDF-"):
        ext = "pdf"
    else:
        ext = "bin"

    # Save each attachment
    output = Path(f"output_{i}.{ext}")
    output.write_bytes(raw)

    print(f"Saved: {output.resolve()}")
