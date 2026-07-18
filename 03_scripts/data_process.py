#!/usr/bin/env python3
# ============================================================
# DATA PROCESSING — Utility Scripts
# ============================================================
"""
เครื่องมือ ETL / data transformation ที่ใช้บ่อย:
  - Pipeline   : chain transformation steps
  - DataCleaner: ทำความสะอาด/validate data
  - Aggregator : group + aggregate
  - Flattener  : flatten nested structures
  - Differ     : เปรียบเทียบ datasets
"""

from __future__ import annotations
from typing import Any, Callable, Iterable, TypeVar, Iterator
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime
import re, json, statistics

T = TypeVar("T")
Record = dict[str, Any]

# ── 1. Pipeline ───────────────────────────────────────────────
class Pipeline:
    """
    Chain data transformations แบบ functional

    Usage:
        result = (Pipeline(data)
                  .map(lambda x: x.strip())
                  .filter(bool)
                  .map(str.upper)
                  .to_list())
    """
    def __init__(self, data: Iterable):
        self._data = iter(data)

    def map(self, fn: Callable) -> "Pipeline":
        self._data = map(fn, self._data)
        return self

    def filter(self, fn: Callable | None = None) -> "Pipeline":
        self._data = filter(fn, self._data)
        return self

    def flat_map(self, fn: Callable) -> "Pipeline":
        def _gen():
            for item in self._data:
                yield from fn(item)
        self._data = _gen()
        return self

    def take(self, n: int) -> "Pipeline":
        from itertools import islice
        self._data = islice(self._data, n)
        return self

    def skip(self, n: int) -> "Pipeline":
        from itertools import islice
        for _ in range(n):
            next(self._data, None)
        return self

    def batch(self, size: int) -> "Pipeline":
        def _batches():
            buf = []
            for item in self._data:
                buf.append(item)
                if len(buf) == size:
                    yield buf
                    buf = []
            if buf:
                yield buf
        self._data = _batches()
        return self

    def unique(self, key: Callable | None = None) -> "Pipeline":
        seen: set = set()
        def _gen():
            for item in self._data:
                k = key(item) if key else item
                if k not in seen:
                    seen.add(k)
                    yield item
        self._data = _gen()
        return self

    def peek(self, fn: Callable | None = None) -> "Pipeline":
        """Side-effect without changing data"""
        fn = fn or print
        def _gen():
            for item in self._data:
                fn(item)
                yield item
        self._data = _gen()
        return self

    def to_list(self) -> list:      return list(self._data)
    def to_set(self) -> set:        return set(self._data)
    def to_dict(self, key: Callable, value: Callable = lambda x: x) -> dict:
        return {key(item): value(item) for item in self._data}
    def first(self) -> Any:         return next(self._data, None)
    def count(self) -> int:         return sum(1 for _ in self._data)

# ── 2. DataCleaner ────────────────────────────────────────────
class DataCleaner:
    """ทำความสะอาด/validate/transform field ใน records"""

    def __init__(self):
        self._rules: list[Callable[[Record], Record | None]] = []
        self._errors: list[dict] = []

    def add_rule(self, rule: Callable[[Record], Record | None]) -> "DataCleaner":
        self._rules.append(rule)
        return self

    def clean(self, records: list[Record]) -> list[Record]:
        result = []
        for i, rec in enumerate(records):
            cleaned = rec.copy()
            ok = True
            for rule in self._rules:
                try:
                    cleaned = rule(cleaned)
                    if cleaned is None:
                        ok = False
                        break
                except Exception as e:
                    self._errors.append({"index": i, "record": rec, "error": str(e)})
                    ok = False
                    break
            if ok and cleaned is not None:
                result.append(cleaned)
        return result

    @property
    def errors(self) -> list[dict]: return self._errors

    # ── Reusable rule builders ────────────────────────────────
    @staticmethod
    def strip_fields(*fields: str) -> Callable:
        def rule(rec: Record) -> Record:
            for f in fields:
                if f in rec and isinstance(rec[f], str):
                    rec[f] = rec[f].strip()
            return rec
        return rule

    @staticmethod
    def require_fields(*fields: str) -> Callable:
        def rule(rec: Record) -> Record | None:
            for f in fields:
                if not rec.get(f):
                    return None
            return rec
        return rule

    @staticmethod
    def cast_field(field: str, fn: Callable, default: Any = None) -> Callable:
        def rule(rec: Record) -> Record:
            try:
                rec[field] = fn(rec[field])
            except (ValueError, TypeError, KeyError):
                rec[field] = default
            return rec
        return rule

    @staticmethod
    def rename_fields(**mapping: str) -> Callable:
        """rename_fields(old_name="new_name")"""
        def rule(rec: Record) -> Record:
            for old, new in mapping.items():
                if old in rec:
                    rec[new] = rec.pop(old)
            return rec
        return rule

    @staticmethod
    def drop_fields(*fields: str) -> Callable:
        def rule(rec: Record) -> Record:
            for f in fields:
                rec.pop(f, None)
            return rec
        return rule

    @staticmethod
    def validate_email(field: str) -> Callable:
        pattern = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]+$")
        def rule(rec: Record) -> Record | None:
            val = rec.get(field, "")
            return rec if pattern.match(str(val)) else None
        return rule

# ── 3. Aggregator ────────────────────────────────────────────
class Aggregator:
    """Group + aggregate records"""

    def __init__(self, records: list[Record]):
        self._records = records

    def group_by(self, *keys: str) -> dict[tuple, list[Record]]:
        groups: dict = defaultdict(list)
        for rec in self._records:
            k = tuple(rec.get(key) for key in keys)
            groups[k].append(rec)
        return dict(groups)

    def agg(
        self,
        group_keys: list[str],
        agg_spec: dict[str, tuple[str, Callable]],
    ) -> list[Record]:
        """
        Aggregate records

        agg_spec = {"total_sales": ("amount", sum),
                    "avg_age":     ("age",    statistics.mean),
                    "count":       ("id",     len)}
        """
        groups  = self.group_by(*group_keys)
        result  = []
        for key_vals, rows in groups.items():
            rec = dict(zip(group_keys, key_vals))
            for out_field, (src_field, fn) in agg_spec.items():
                values = [r[src_field] for r in rows if src_field in r]
                rec[out_field] = fn(values) if values else None
            result.append(rec)
        return result

# ── 4. Flattener ─────────────────────────────────────────────
def flatten_dict(d: dict, sep: str = ".", prefix: str = "") -> dict:
    """
    Flatten nested dict

    {"user": {"name": "Alice", "addr": {"city": "BKK"}}}
    → {"user.name": "Alice", "user.addr.city": "BKK"}
    """
    result = {}
    for k, v in d.items():
        full_key = f"{prefix}{sep}{k}" if prefix else k
        if isinstance(v, dict):
            result.update(flatten_dict(v, sep, full_key))
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    result.update(flatten_dict(item, sep, f"{full_key}[{i}]"))
                else:
                    result[f"{full_key}[{i}]"] = item
        else:
            result[full_key] = v
    return result

def unflatten_dict(d: dict, sep: str = ".") -> dict:
    """ย้อนกลับจาก flat dict → nested dict"""
    result: dict = {}
    for key, value in d.items():
        parts = key.split(sep)
        node  = result
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value
    return result

# ── 5. Differ ────────────────────────────────────────────────
@dataclass
class DiffResult:
    added:   list[Record] = field(default_factory=list)
    removed: list[Record] = field(default_factory=list)
    changed: list[dict]   = field(default_factory=list)
    unchanged: list[Record] = field(default_factory=list)

    def summary(self) -> str:
        return (f"Added: {len(self.added)}, Removed: {len(self.removed)}, "
                f"Changed: {len(self.changed)}, Unchanged: {len(self.unchanged)}")

def diff_records(
    old: list[Record],
    new: list[Record],
    key: str,
    compare_fields: list[str] | None = None,
) -> DiffResult:
    """เปรียบเทียบ dataset สองชุด"""
    old_map = {r[key]: r for r in old}
    new_map = {r[key]: r for r in new}
    result  = DiffResult()

    for k, new_rec in new_map.items():
        if k not in old_map:
            result.added.append(new_rec)
        else:
            old_rec = old_map[k]
            fields  = compare_fields or list(new_rec.keys())
            changes = {f: {"old": old_rec.get(f), "new": new_rec.get(f)}
                       for f in fields
                       if old_rec.get(f) != new_rec.get(f)}
            if changes:
                result.changed.append({key: k, "changes": changes})
            else:
                result.unchanged.append(new_rec)

    for k in old_map:
        if k not in new_map:
            result.removed.append(old_map[k])

    return result

# ── Demo ──────────────────────────────────────────────────────
if __name__ == "__main__":
    # Pipeline
    data = ["  Alice ", "  Bob ", "", "  charlie ", "  ALICE  "]
    result = (Pipeline(data)
              .map(str.strip)
              .filter(bool)
              .map(str.lower)
              .unique()
              .to_list())
    print("Pipeline:", result)

    # DataCleaner
    raw = [
        {"name": "  Alice  ", "age": "30", "email": "alice@example.com"},
        {"name": "Bob",       "age": "abc", "email": "not-an-email"},
        {"name": "",          "age": "25", "email": "charlie@example.com"},
    ]
    cleaner = (DataCleaner()
               .add_rule(DataCleaner.strip_fields("name"))
               .add_rule(DataCleaner.require_fields("name"))
               .add_rule(DataCleaner.cast_field("age", int, default=0))
               .add_rule(DataCleaner.validate_email("email")))
    clean = cleaner.clean(raw)
    print("\nCleaned:", clean)

    # Aggregator
    sales = [
        {"region": "North", "category": "A", "amount": 100},
        {"region": "North", "category": "B", "amount": 200},
        {"region": "South", "category": "A", "amount": 150},
        {"region": "North", "category": "A", "amount": 80},
    ]
    agg = Aggregator(sales).agg(
        group_keys=["region"],
        agg_spec={"total": ("amount", sum), "count": ("amount", len)}
    )
    print("\nAggregated:", agg)

    # Flatten
    nested = {"user": {"name": "Alice", "addr": {"city": "Bangkok", "zip": "10100"}}}
    flat   = flatten_dict(nested)
    print("\nFlattened:", flat)
    print("Unflattened:", unflatten_dict(flat))

    # Diff
    old_data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    new_data = [{"id": 1, "name": "Alicia"}, {"id": 3, "name": "Charlie"}]
    diff = diff_records(old_data, new_data, key="id")
    print("\nDiff:", diff.summary())
    print("Changed:", diff.changed)
