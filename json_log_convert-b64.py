
import argparse
import base64
import binascii
import json
import re
import hashlib
from pathlib import Path
from urllib.parse import unquote_to_bytes


# Identify common file types using their binary signatures
def detect_file_type(raw, mime=""):
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if raw.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if raw.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if raw.startswith(b"RIFF") and raw[8:12] == b"WEBP":
        return "webp"
    if raw.startswith(b"%PDF-"):
        return "pdf"
    if raw.startswith(b"BM"):
        return "bmp"
    if raw.startswith((b"II*\x00", b"MM\x00*")):
        return "tif"
    if raw.startswith(b"PK\x03\x04"):
        return "zip"
    if raw.startswith(b"\x1f\x8b"):
        return "gz"
    if raw.startswith(b"Rar!\x1a\x07"):
        return "rar"
    if raw.startswith(b"7z\xbc\xaf\x27\x1c"):
        return "7z"
    if raw.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return "ole"

    mime_map = {
        "image/png": "png",
        "image/jpeg": "jpg",
        "image/gif": "gif",
        "image/webp": "webp",
        "application/pdf": "pdf",
        "application/zip": "zip",
    }

    return mime_map.get(mime.lower(), None)


def decode_candidate(value):
    """Return decoded bytes and MIME type if the value looks encoded."""
    mime = ""

    if not isinstance(value, str):
        return None, mime

    value = value.strip()
    if not value:
        return None, mime

    # Handle data:image/png;base64,... and other data URIs
    if value.startswith("data:") and "," in value:
        header, value = value.split(",", 1)
        mime = header[5:].split(";")[0]

        if ";base64" not in header.lower():
            return unquote_to_bytes(value), mime

    # Remove whitespace and try Base64 decoding
    compact = re.sub(r"\s+", "", value)

    # Ignore ordinary text and short strings
    if len(compact) < 32:
        return None, mime

    try:
        raw = base64.b64decode(compact, validate=True)
        if raw:
            return raw, mime
    except (binascii.Error, ValueError):
        pass

    return None, mime


def walk_json(obj, path="$"):
    """Recursively locate encoded files in dictionaries and lists."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield from walk_json(value, f"{path}.{key}")

    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from walk_json(value, f"{path}[{index}]")

    elif isinstance(obj, str):
        raw, mime = decode_candidate(obj)

        if raw is not None:
            extension = detect_file_type(raw, mime)

            # Only accept recognized formats, or likely Base64 fields
            # with a valid Base64 payload but an unknown signature.
            key_name = path.rsplit(".", 1)[-1].lower()
            likely_file_field = any(
                word in key_name
                for word in (
                    "base64", "archivo", "filecontent",
                    "file_content", "attachment", "document"
                )
            )

            if extension or likely_file_field:
                yield path, raw, extension or "bin"


def main():
    parser = argparse.ArgumentParser(
        description="Extract Base64-encoded files from any JSON structure."
    )
    parser.add_argument("input", help="Path to the input JSON file")
    parser.add_argument(
        "-o", "--output",
        default="decoded_files",
        help="Output directory (default: decoded_files)"
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8-sig") as f:
        data = json.load(f)

    found = 0
    seen = set()

    for json_path, raw, extension in walk_json(data):
        # Avoid saving identical files more than once
        digest = hashlib.sha256(raw).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)

        found += 1
        output_path = output_dir / f"file_{found}.{extension}"
        output_path.write_bytes(raw)

        print(f"[+] Saved: {output_path} ({len(raw)} bytes)")
        print(f"    JSON path: {json_path}")

    if found == 0:
        print("[-] No recognizable encoded files found.")
        print("    Check whether the JSON contains Base64 data.")

    else:
        print(f"\nCompleted: extracted {found} file(s).")
        print(f"Output directory: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
