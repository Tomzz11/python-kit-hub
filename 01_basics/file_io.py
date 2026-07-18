# ============================================================
# FILE I/O — Python Reference
# ============================================================
import json
import csv
import os
import pathlib
from pathlib import Path
from typing import Generator

# ── 1. Text file read/write ──────────────────────────────────
def write_text(path: str, content: str, mode: str = "w"):
    """Write text to file"""
    with open(path, mode, encoding="utf-8") as f:
        f.write(content)

def read_text(path: str) -> str:
    """Read entire file"""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def read_lines(path: str) -> list[str]:
    """Read file as list of lines"""
    with open(path, "r", encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f]

def read_lines_lazy(path: str) -> Generator[str, None, None]:
    """Read lines lazily (ประหยัด memory สำหรับไฟล์ใหญ่)"""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            yield line.rstrip("\n")

# ── 2. JSON ──────────────────────────────────────────────────
def save_json(path: str, data: dict | list, indent: int = 2):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)

def load_json(path: str) -> dict | list:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# JSON string <-> object
def to_json_str(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)

def from_json_str(s: str) -> dict:
    return json.loads(s)

# ── 3. CSV ───────────────────────────────────────────────────
def write_csv(path: str, rows: list[dict], fieldnames: list[str] | None = None):
    if not rows:
        return
    fieldnames = fieldnames or list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def read_csv(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

# ── 4. pathlib (แนะนำ) ───────────────────────────────────────
def pathlib_examples():
    base = Path(".")

    # สร้างโฟลเดอร์
    output_dir = base / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # เขียน/อ่านไฟล์
    p = output_dir / "demo.txt"
    p.write_text("Hello, pathlib!", encoding="utf-8")
    content = p.read_text(encoding="utf-8")
    print(content)

    # File info
    print(p.name)        # demo.txt
    print(p.stem)        # demo
    print(p.suffix)      # .txt
    print(p.parent)      # output
    print(p.exists())    # True
    print(p.stat().st_size)  # bytes

    # List files
    py_files = list(base.glob("**/*.py"))

    # Rename / move
    new_path = p.with_suffix(".md")
    p.rename(new_path)

    # Delete
    new_path.unlink(missing_ok=True)
    output_dir.rmdir()

# ── 5. os operations ─────────────────────────────────────────
def os_examples():
    # Environment variables
    home    = os.environ.get("HOME", "/tmp")
    api_key = os.getenv("API_KEY", "default")

    # Path operations (prefer pathlib)
    full = os.path.join("/usr", "local", "bin", "python")
    exists  = os.path.exists(full)
    is_file = os.path.isfile(full)
    is_dir  = os.path.isdir(full)

    # Walk directory tree
    for root, dirs, files in os.walk("."):
        level = root.count(os.sep)
        indent = " " * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        for f in files:
            print(f"{indent}  {f}")

# ── 6. Binary file ───────────────────────────────────────────
def copy_file_chunks(src: str, dst: str, chunk_size: int = 65536):
    """Copy ไฟล์แบบ chunk เหมาะกับไฟล์ใหญ่"""
    with open(src, "rb") as fin, open(dst, "wb") as fout:
        while chunk := fin.read(chunk_size):
            fout.write(chunk)

# ── 7. Temporary file ────────────────────────────────────────
import tempfile

def process_with_temp():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt",
                                     delete=False, encoding="utf-8") as tmp:
        tmp.write("temporary content")
        tmp_path = tmp.name
    try:
        content = Path(tmp_path).read_text(encoding="utf-8")
        return content
    finally:
        Path(tmp_path).unlink(missing_ok=True)

# ── Demo ──────────────────────────────────────────────────────
if __name__ == "__main__":
    # Text
    write_text("/tmp/test.txt", "Hello, World!\nLine 2\n")
    print(read_text("/tmp/test.txt"))
    print(read_lines("/tmp/test.txt"))

    # JSON
    data = {"name": "Alice", "scores": [90, 85, 92], "active": True}
    save_json("/tmp/test.json", data)
    loaded = load_json("/tmp/test.json")
    print(loaded)

    # CSV
    people = [
        {"name": "Alice", "age": 30, "city": "Bangkok"},
        {"name": "Bob",   "age": 25, "city": "Chiang Mai"},
    ]
    write_csv("/tmp/test.csv", people)
    print(read_csv("/tmp/test.csv"))

    # Temp file
    print(process_with_temp())

    # Cleanup
    for f in ["/tmp/test.txt", "/tmp/test.json", "/tmp/test.csv"]:
        Path(f).unlink(missing_ok=True)
