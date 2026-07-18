# ============================================================
# CONCURRENCY — Python Reference
# ============================================================
import asyncio
import threading
import concurrent.futures
import time
from typing import Callable, Any
from queue import Queue

# ══════════════════════════════════════════════════════════════
# PART A — ASYNC / AWAIT (I/O-bound tasks)
# ══════════════════════════════════════════════════════════════

# ── A1. Basic coroutine ──────────────────────────────────────
async def fetch_data(url: str, delay: float = 1.0) -> dict:
    """Simulate HTTP request"""
    print(f"  → Fetching {url}")
    await asyncio.sleep(delay)       # non-blocking wait
    print(f"  ← Done {url}")
    return {"url": url, "data": f"response from {url}"}

async def main_sequential():
    """Sequential: total ~3s"""
    r1 = await fetch_data("api.example.com/users",    1.0)
    r2 = await fetch_data("api.example.com/products", 1.0)
    r3 = await fetch_data("api.example.com/orders",   1.0)
    return [r1, r2, r3]

async def main_concurrent():
    """Concurrent: total ~1s (fastest wins)"""
    results = await asyncio.gather(
        fetch_data("api.example.com/users",    1.0),
        fetch_data("api.example.com/products", 0.8),
        fetch_data("api.example.com/orders",   1.2),
    )
    return results

# ── A2. asyncio.gather with error handling ───────────────────
async def safe_fetch(url: str) -> dict | None:
    try:
        return await fetch_data(url, 0.5)
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None

async def fetch_all_safe(urls: list[str]) -> list:
    tasks   = [safe_fetch(u) for u in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if r is not None]

# ── A3. async context manager ────────────────────────────────
class AsyncDBConnection:
    async def __aenter__(self):
        print("  DB: connecting...")
        await asyncio.sleep(0.1)
        return self

    async def __aexit__(self, *args):
        print("  DB: disconnecting")

    async def query(self, sql: str) -> list:
        await asyncio.sleep(0.05)
        return [{"id": 1}, {"id": 2}]

async def use_db():
    async with AsyncDBConnection() as db:
        rows = await db.query("SELECT * FROM users")
        return rows

# ── A4. async generator ──────────────────────────────────────
async def arange(start: int, stop: int, step: int = 1):
    current = start
    while current < stop:
        await asyncio.sleep(0)   # yield control
        yield current
        current += step

async def consume_generator():
    results = []
    async for n in arange(0, 10, 2):
        results.append(n)
    return results

# ── A5. Producer-consumer with asyncio.Queue ─────────────────
async def producer(queue: asyncio.Queue, items: list):
    for item in items:
        await asyncio.sleep(0.1)
        await queue.put(item)
        print(f"  Produced: {item}")
    await queue.put(None)   # sentinel

async def consumer(queue: asyncio.Queue) -> list:
    results = []
    while True:
        item = await queue.get()
        if item is None:
            break
        print(f"  Consumed: {item}")
        results.append(item * 2)
    return results

async def producer_consumer_demo():
    queue = asyncio.Queue(maxsize=3)
    prod  = asyncio.create_task(producer(queue, [1,2,3,4,5]))
    cons  = asyncio.create_task(consumer(queue))
    await prod
    return await cons

# ── A6. Timeout ──────────────────────────────────────────────
async def with_timeout():
    try:
        result = await asyncio.wait_for(fetch_data("slow.example.com", 5.0), timeout=1.5)
    except asyncio.TimeoutError:
        print("  Request timed out!")
        result = None
    return result

# ── A7. Semaphore (rate limiting) ────────────────────────────
async def rate_limited_fetch(semaphore: asyncio.Semaphore, url: str) -> dict:
    async with semaphore:
        return await fetch_data(url, 0.2)

async def fetch_with_limit(urls: list[str], max_concurrent: int = 3):
    sem  = asyncio.Semaphore(max_concurrent)
    tasks = [rate_limited_fetch(sem, u) for u in urls]
    return await asyncio.gather(*tasks)

# ══════════════════════════════════════════════════════════════
# PART B — THREADING (I/O-bound, legacy APIs)
# ══════════════════════════════════════════════════════════════

# ── B1. Basic thread ─────────────────────────────────────────
def cpu_task(name: str, n: int) -> int:
    time.sleep(0.1)   # simulate I/O
    return sum(range(n))

def threading_demo():
    results: dict = {}
    lock = threading.Lock()

    def worker(name: str, n: int):
        result = cpu_task(name, n)
        with lock:
            results[name] = result
            print(f"  {name}: {result}")

    threads = [
        threading.Thread(target=worker, args=(f"task-{i}", i * 1000))
        for i in range(5)
    ]
    for t in threads: t.start()
    for t in threads: t.join()
    return results

# ── B2. ThreadPoolExecutor ───────────────────────────────────
def thread_pool_demo():
    urls = [f"https://example.com/page/{i}" for i in range(10)]

    def fetch_sync(url: str) -> str:
        time.sleep(0.1)   # simulate blocking I/O
        return f"content of {url}"

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures  = {executor.submit(fetch_sync, url): url for url in urls}
        results  = {}
        for future in concurrent.futures.as_completed(futures):
            url = futures[future]
            try:
                results[url] = future.result()
            except Exception as e:
                print(f"  {url} failed: {e}")
    return results

# ── B3. ProcessPoolExecutor (CPU-bound) ──────────────────────
def cpu_intensive(n: int) -> int:
    """CPU-bound task — ใช้ ProcessPool ไม่ใช่ ThreadPool"""
    return sum(i * i for i in range(n))

def process_pool_demo():
    inputs = [1_000_000] * 4
    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = list(executor.map(cpu_intensive, inputs))
    return results

# ── B4. Thread-safe Queue ────────────────────────────────────
def queue_demo():
    q: Queue = Queue(maxsize=5)

    def producer():
        for i in range(10):
            q.put(i)
            print(f"  Put: {i}")
        q.put(None)   # sentinel

    def consumer():
        results = []
        while True:
            item = q.get()
            if item is None:
                break
            results.append(item)
            q.task_done()
        return results

    t_prod = threading.Thread(target=producer)
    t_cons = threading.Thread(target=consumer)
    t_prod.start()
    t_cons.start()
    t_prod.join()
    t_cons.join()

# ── Demo ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== Async Concurrent Fetch ===")
    results = asyncio.run(main_concurrent())
    print(f"Got {len(results)} results\n")

    print("=== Producer-Consumer ===")
    items = asyncio.run(producer_consumer_demo())
    print(f"Processed: {items}\n")

    print("=== Thread Pool ===")
    threading_demo()

    # NOTE: process_pool_demo() needs __main__ guard (already here)
    # Uncomment to test CPU-bound:
    # print(process_pool_demo())
