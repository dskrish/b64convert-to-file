# JSON Base64 File Extractor

A small, dependency-free Python CLI that scans JSON files for Base64-encoded file content, detects common file formats, and writes extracted files to an output directory.

It is designed for JSON responses with arbitrary nesting, including structures such as:

```json
{
  "NroDelivery": "12345",
  "Archivos": [
    {
      "ArchivoBase64": "<base64-content>",
      "NombreArchivo": "documento.jpg"
    }
  ]
}
```

The script does not require a fixed property name or JSON layout. It recursively traverses dictionaries and lists.

## Features

- Recursively searches nested JSON objects and arrays.
- Handles Base64 strings and `data:` URIs such as `data:image/png;base64,...`.
- Detects common file formats from file signatures (PNG, JPEG, GIF, WebP, BMP, TIFF, PDF, ZIP, GZIP, RAR, 7z, and OLE).
- Supports likely file-content field names such as `base64`, `archivo`, `filecontent`, `file_content`, `attachment`, and `document` when the file type is not recognized.
- Avoids writing duplicate file contents more than once.
- Prints the JSON path where each extracted payload was found.
- Uses only the Python standard library. No third-party packages are required.

## Requirements

- Python 3.9 or newer recommended.
- A JSON input file containing Base64-encoded file content.

## Usage

### Basic usage

```bash
python json_file_extractor.py input.json
```

Extracted files are written to `decoded_files/` by default.

### Choose an output directory

```bash
python json_file_extractor.py input.json --output extracted
```

Short option:

```bash
python json_file_extractor.py input.json -o extracted
```

### Windows PowerShell example

```powershell
python .\json_file_extractor.py "C:\path\to\response.json" -o "C:\path\to\extracted"
```

### Linux / macOS example

```bash
python3 json_file_extractor.py ./response.json --output ./extracted
```

## Example

A sample input is provided at [`examples/sample.json`](examples/sample.json). Run:

```bash
python json_file_extractor.py examples/sample.json -o output
```

The script should identify the embedded PNG and save it to the output folder. The sample uses a tiny, non-sensitive test image.

Example output:

```text
[+] Saved: output/file_1.png (68 bytes)
    JSON path: $.Archivos[0].ArchivoBase64

Completed: extracted 1 file(s).
Output directory: .../output
```

Exact file sizes and paths can vary by platform and changes to the sample.

## How it works

1. Loads the JSON document.
2. Recursively walks dictionaries and lists.
3. Attempts Base64 decoding for string values (and decodes Base64 data URIs).
4. Detects the format using file signatures and, for unknown formats, checks whether the JSON key looks like a file-content field.
5. Saves accepted payloads using generated names such as `file_1.jpg` or `file_2.pdf`.
6. Uses SHA-256 hashes to skip duplicate payloads.

## Limitations

- This is a heuristic extractor, not a universal file detector. It can miss non-standard encodings, Base64 strings split across multiple fields, encrypted/compressed application-specific payloads, or payloads that are not represented as strings.
- Unknown formats are saved as `.bin` only when the containing key looks like a file-content field.
- The extractor does not execute extracted files.
- JSON strings that themselves contain serialized JSON are not parsed recursively in this version.
- The extractor does not recover an original filename unless you extend it to read filename metadata. It uses safe generated names instead.
- Base64 decoding is not a malware scan. Treat extracted files as untrusted.
