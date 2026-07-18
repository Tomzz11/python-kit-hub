#!/usr/bin/env python3
# ============================================================
# FILE TOOLS — Utility Scripts
# ============================================================
"""
เครื่องมือจัดการไฟล์และโฟลเดอร์ที่ใช้บ่อย:
  - find_files      : ค้นหาไฟล์ตาม pattern
  - bulk_rename     : rename ไฟล์หลายไฟล์พร้อมกัน
  - tree            : แสดงโครงสร้างโฟลเดอร์
  - du              : วิเคราะห์ขนาดไฟล์
  - sync_dirs       : sync โฟลเดอร์
  - watch_dir       : monitor การเปลี่ยนแปลง
"""

import os
import re
import shutil
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from typing import Iterator, Callable

# ── 1. find_files ────────────────────────────────────────────
def find_files(
    root: str | Path,
    pattern: str = "*",
    recursive: bool = True,
    min_size: int = 0,
    max_size: int | None = None,
    newer_than: datetime | None = None,
    exclude_dirs: list[str] | None = None,
) -> Iterator[Path]:
    """
    ค้นหาไฟล์ตาม criteria ต่างๆ

    Args:
        root:        โฟลเดอร์เริ่มต้น
        pattern:     glob pattern เช่น "*.py", "*.{jpg,png}"
        recursive:   ค้นหาใน subdirectory ด้วย
        min_size:    ขนาดขั้นต่ำ (bytes)
        max_size:    ขนาดสูงสุด (bytes)
        newer_than:  ไฟล์ที่แก้ไขหลังจากวันนี้
        exclude_dirs: ชื่อโฟลเดอร์ที่ข้าม เช่น [".git", "node_modules"]

    Yields:
        Path ของไฟล์ที่ตรงเงื่อนไข
    """
    root = Path(root)
    exclude_dirs = set(exclude_dirs or [".git", "__pycache__", "node_modules"])
    glob_fn = root.rglob if recursive else root.glob

    for p in glob_fn(pattern):
        if not p.is_file():
            continue
        if any(part in exclude_dirs for part in p.parts):
            continue
        stat = p.stat()
        if stat.st_size < min_size:
            continue
        if max_size is not None and stat.st_size > max_size:
            continue
        if newer_than and datetime.fromtimestamp(stat.st_mtime) < newer_than:
            continue
        yield p

# ── 2. bulk_rename ───────────────────────────────────────────
def bulk_rename(
    directory: str | Path,
    pattern: str,
    replacement: str,
    dry_run: bool = True,
    recursive: bool = False,
) -> list[tuple[Path, Path]]:
    """
    Rename ไฟล์หลายไฟล์โดยใช้ regex

    Args:
        directory:   โฟลเดอร์ที่จะ rename
        pattern:     regex pattern ของชื่อไฟล์
        replacement: ชื่อใหม่ (รองรับ back-reference เช่น \\1)
        dry_run:     True = แค่แสดงผล ไม่ได้ rename จริง
        recursive:   rename ใน subdirectory ด้วย

    Returns:
        list ของ (old_path, new_path)
    """
    directory = Path(directory)
    renames   = []
    glob_fn   = directory.rglob("*") if recursive else directory.iterdir()

    for p in sorted(glob_fn):
        if not p.is_file():
            continue
        new_name = re.sub(pattern, replacement, p.name)
        if new_name == p.name:
            continue
        new_path = p.parent / new_name
        renames.append((p, new_path))
        if dry_run:
            print(f"  [DRY] {p.name!r} → {new_name!r}")
        else:
            p.rename(new_path)
            print(f"  {p.name!r} → {new_name!r}")

    return renames

# ── 3. tree ──────────────────────────────────────────────────
def tree(
    root: str | Path,
    max_depth: int = 3,
    show_hidden: bool = False,
    show_size: bool = True,
) -> str:
    """
    แสดงโครงสร้างโฟลเดอร์แบบ tree command

    Returns:
        string ของ tree
    """
    root  = Path(root)
    lines = [str(root)]

    def _walk(path: Path, prefix: str, depth: int):
        if depth > max_depth:
            return
        entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name))
        entries = [e for e in entries if show_hidden or not e.name.startswith(".")]
        for i, entry in enumerate(entries):
            is_last    = (i == len(entries) - 1)
            connector  = "└── " if is_last else "├── "
            sub_prefix = prefix + ("    " if is_last else "│   ")
            if show_size and entry.is_file():
                size = _human_size(entry.stat().st_size)
                lines.append(f"{prefix}{connector}{entry.name} ({size})")
            else:
                lines.append(f"{prefix}{connector}{entry.name}")
            if entry.is_dir():
                _walk(entry, sub_prefix, depth + 1)

    _walk(root, "", 1)
    return "\n".join(lines)

def _human_size(n: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.0f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"

# ── 4. du (disk usage) ───────────────────────────────────────
def du(root: str | Path, top_n: int = 10) -> list[tuple[Path, int]]:
    """
    วิเคราะห์ขนาดไฟล์/โฟลเดอร์ (disk usage)

    Returns:
        list ของ (path, size_bytes) เรียงจากใหญ่ไปเล็ก
    """
    root   = Path(root)
    sizes  = []

    def _dir_size(p: Path) -> int:
        return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())

    for entry in root.iterdir():
        if entry.is_file():
            sizes.append((entry, entry.stat().st_size))
        elif entry.is_dir():
            sizes.append((entry, _dir_size(entry)))

    sizes.sort(key=lambda x: x[1], reverse=True)
    return sizes[:top_n]

# ── 5. file_hash ─────────────────────────────────────────────
def file_hash(path: str | Path, algorithm: str = "sha256") -> str:
    """คำนวณ hash ของไฟล์"""
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def find_duplicates(directory: str | Path) -> dict[str, list[Path]]:
    """ค้นหาไฟล์ที่ซ้ำกันใน directory"""
    hashes: dict[str, list[Path]] = {}
    for p in Path(directory).rglob("*"):
        if p.is_file():
            h = file_hash(p)
            hashes.setdefault(h, []).append(p)
    return {h: paths for h, paths in hashes.items() if len(paths) > 1}

# ── 6. sync_dirs ─────────────────────────────────────────────
def sync_dirs(src: str | Path, dst: str | Path, dry_run: bool = True) -> dict:
    """
    Sync โฟลเดอร์ src → dst (คล้าย rsync)

    Returns:
        {"copied": [...], "updated": [...], "deleted": [...]}
    """
    src, dst = Path(src), Path(dst)
    dst.mkdir(parents=True, exist_ok=True)
    result  = {"copied": [], "updated": [], "deleted": []}

    # copy/update
    for src_file in src.rglob("*"):
        if not src_file.is_file():
            continue
        dst_file = dst / src_file.relative_to(src)
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        if not dst_file.exists():
            action = "COPY"
            result["copied"].append(dst_file)
        elif src_file.stat().st_mtime > dst_file.stat().st_mtime:
            action = "UPDATE"
            result["updated"].append(dst_file)
        else:
            continue
        print(f"  [{action}] {src_file.relative_to(src)}")
        if not dry_run:
            shutil.copy2(src_file, dst_file)

    return result

# ── CLI ───────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="File Tools")
    sub    = parser.add_subparsers(dest="command")

    # tree command
    p_tree = sub.add_parser("tree", help="Show directory tree")
    p_tree.add_argument("path",  default=".", nargs="?")
    p_tree.add_argument("--depth", "-d", type=int, default=3)
    p_tree.add_argument("--no-size", action="store_true")

    # find command
    p_find = sub.add_parser("find", help="Find files")
    p_find.add_argument("path",    default=".", nargs="?")
    p_find.add_argument("--pattern", "-p", default="*")
    p_find.add_argument("--min-size", type=int, default=0)

    # du command
    p_du = sub.add_parser("du", help="Disk usage")
    p_du.add_argument("path", default=".", nargs="?")
    p_du.add_argument("--top", type=int, default=10)

    args = parser.parse_args()

    if args.command == "tree":
        print(tree(args.path, args.depth, show_size=not args.no_size))
    elif args.command == "find":
        for f in find_files(args.path, args.pattern, min_size=args.min_size):
            print(f)
    elif args.command == "du":
        for path, size in du(args.path, args.top):
            print(f"{_human_size(size):>8}  {path}")
    else:
        # Demo
        print(tree(".", max_depth=2))

if __name__ == "__main__":
    main()
