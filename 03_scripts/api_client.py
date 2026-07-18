#!/usr/bin/env python3
# ============================================================
# API CLIENT — Utility Scripts
# ============================================================
"""
HTTP API client พร้อม:
  - retry + exponential backoff
  - rate limiting
  - authentication (Bearer, Basic, API Key)
  - response caching
  - pagination helper
"""

import time
import base64
import hashlib
import json
import urllib.request
import urllib.parse
import urllib.error
from dataclasses import dataclass, field
from typing import Any, Iterator
from functools import wraps

# ── 1. APIError ───────────────────────────────────────────────
class APIError(Exception):
    def __init__(self, status: int, message: str, body: Any = None):
        super().__init__(f"HTTP {status}: {message}")
        self.status  = status
        self.message = message
        self.body    = body

class RateLimitError(APIError): pass
class AuthError(APIError):      pass
class NotFoundError(APIError):  pass

# ── 2. Response ───────────────────────────────────────────────
@dataclass
class Response:
    status:  int
    headers: dict
    body:    Any
    elapsed: float

    @property
    def ok(self) -> bool: return 200 <= self.status < 300

    def raise_for_status(self):
        if self.ok:
            return
        msg  = str(self.body)[:200] if self.body else ""
        errs = {401: AuthError, 403: AuthError,
                404: NotFoundError, 429: RateLimitError}
        cls  = errs.get(self.status, APIError)
        raise cls(self.status, msg, self.body)

# ── 3. APIClient ─────────────────────────────────────────────
class APIClient:
    """
    Lightweight HTTP client (stdlib only — ไม่ต้อง install requests)
    สำหรับใช้ requests ให้แทนที่ _send() ด้วย requests.request()
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        headers: dict | None = None,
    ):
        self.base_url      = base_url.rstrip("/")
        self.timeout       = timeout
        self.max_retries   = max_retries
        self.backoff_factor = backoff_factor
        self._headers: dict = {"Content-Type": "application/json",
                               "Accept": "application/json",
                               **(headers or {})}
        self._cache: dict[str, tuple[float, Response]] = {}
        self._cache_ttl = 60.0   # seconds

    # ── Authentication ───────────────────────────────────────
    def set_bearer_token(self, token: str):
        self._headers["Authorization"] = f"Bearer {token}"

    def set_basic_auth(self, username: str, password: str):
        encoded = base64.b64encode(f"{username}:{password}".encode()).decode()
        self._headers["Authorization"] = f"Basic {encoded}"

    def set_api_key(self, key: str, header: str = "X-API-Key"):
        self._headers[header] = key

    # ── Core request ────────────────────────────────────────
    def request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        body: Any = None,
        headers: dict | None = None,
        use_cache: bool = False,
        cache_ttl: float | None = None,
    ) -> Response:
        url = self._build_url(path, params)

        # Cache check (GET only)
        if use_cache and method.upper() == "GET":
            cached = self._get_cache(url)
            if cached:
                return cached

        merged_headers = {**self._headers, **(headers or {})}
        data = json.dumps(body).encode() if body is not None else None

        for attempt in range(self.max_retries + 1):
            try:
                resp = self._send(method, url, merged_headers, data)
                if use_cache and method.upper() == "GET" and resp.ok:
                    self._set_cache(url, resp, cache_ttl or self._cache_ttl)
                return resp
            except (urllib.error.URLError, TimeoutError) as e:
                if attempt == self.max_retries:
                    raise APIError(0, f"Network error: {e}")
                wait = self.backoff_factor * (2 ** attempt)
                print(f"  Retry {attempt+1}/{self.max_retries} in {wait:.1f}s...")
                time.sleep(wait)

    def get(self, path: str, **kw)        -> Response: return self.request("GET",    path, **kw)
    def post(self, path: str, **kw)       -> Response: return self.request("POST",   path, **kw)
    def put(self, path: str, **kw)        -> Response: return self.request("PUT",    path, **kw)
    def patch(self, path: str, **kw)      -> Response: return self.request("PATCH",  path, **kw)
    def delete(self, path: str, **kw)     -> Response: return self.request("DELETE", path, **kw)

    # ── Pagination helper ────────────────────────────────────
    def paginate(
        self,
        path: str,
        params: dict | None = None,
        page_key: str = "page",
        data_key: str = "data",
        total_key: str = "total",
        page_size: int = 100,
    ) -> Iterator[Any]:
        """ดึงข้อมูลทีละหน้าจนครบ"""
        params  = {**(params or {}), "per_page": page_size, page_key: 1}
        seen    = 0
        while True:
            resp = self.get(path, params=params)
            resp.raise_for_status()
            items  = resp.body.get(data_key, [])
            total  = resp.body.get(total_key, 0)
            for item in items:
                yield item
            seen += len(items)
            if not items or seen >= total:
                break
            params[page_key] += 1

    # ── Internals ────────────────────────────────────────────
    def _build_url(self, path: str, params: dict | None) -> str:
        url = f"{self.base_url}/{path.lstrip('/')}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        return url

    def _send(self, method: str, url: str, headers: dict, data: bytes | None) -> Response:
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        start = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                raw     = r.read()
                elapsed = time.perf_counter() - start
                body    = json.loads(raw) if raw else None
                return Response(r.status, dict(r.headers), body, elapsed)
        except urllib.error.HTTPError as e:
            raw     = e.read()
            elapsed = time.perf_counter() - start
            body    = json.loads(raw) if raw else None
            return Response(e.code, dict(e.headers), body, elapsed)

    def _get_cache(self, url: str) -> Response | None:
        if url in self._cache:
            exp, resp = self._cache[url]
            if time.time() < exp:
                return resp
            del self._cache[url]
        return None

    def _set_cache(self, url: str, resp: Response, ttl: float):
        self._cache[url] = (time.time() + ttl, resp)

# ── 4. Convenience functions ─────────────────────────────────
def get_json(url: str, headers: dict | None = None, timeout: float = 10) -> Any:
    """Quick GET ไม่ต้องสร้าง client"""
    req = urllib.request.Request(url, headers={"Accept": "application/json",
                                               **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())

def post_json(url: str, body: dict, headers: dict | None = None, timeout: float = 10) -> Any:
    """Quick POST"""
    data = json.dumps(body).encode()
    req  = urllib.request.Request(
        url, data=data, method="POST",
        headers={"Content-Type": "application/json",
                 "Accept": "application/json", **(headers or {})}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())

# ── Demo ──────────────────────────────────────────────────────
if __name__ == "__main__":
    # ตัวอย่าง: ใช้กับ JSONPlaceholder (public test API)
    client = APIClient("https://jsonplaceholder.typicode.com")

    # GET
    resp = client.get("/users/1")
    resp.raise_for_status()
    print(f"User: {resp.body['name']} | elapsed: {resp.elapsed*1000:.0f}ms")

    # GET with cache
    resp1 = client.get("/posts/1", use_cache=True)
    resp2 = client.get("/posts/1", use_cache=True)   # from cache
    print(f"Post title: {resp1.body['title'][:40]}...")

    # POST
    new_post = {"title": "Hello", "body": "World", "userId": 1}
    resp = client.post("/posts", body=new_post)
    print(f"Created post id: {resp.body['id']}")

    # Pagination (ดึงครั้งละ 10 จาก 100 records)
    all_todos = list(client.paginate("/todos",
                                     params={"userId": 1},
                                     data_key="",     # ไม่มี wrapper
                                     page_size=5))
    print(f"Total todos: {len(all_todos)}")

    # Quick functions
    data = get_json("https://jsonplaceholder.typicode.com/users/2")
    print(f"Quick GET: {data['email']}")
