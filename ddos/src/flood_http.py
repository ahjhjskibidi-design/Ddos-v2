#!/usr/bin/env python3
import asyncio, aiohttp, argparse, time, random, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils import ua, load_lines

counter = 0
lock = asyncio.Lock()

async def worker(url, proxy, sem, timeout):
    global counter
    headers = {"User-Agent": ua(), "Accept": "*/*", "Connection": "keep-alive"}
    conn = aiohttp.TCPConnector(limit=0, ttl_dns_cache=300, force_close=False)
    async with sem:
        async with aiohttp.ClientSession(connector=conn, timeout=aiohttp.ClientTimeout(total=timeout)) as s:
            while True:
                try:
                    async with s.get(url, headers=headers, proxy=proxy, ssl=False) as r:
                        await r.read()
                    async with lock:
                        counter += 1
                except Exception:
                    pass

async def stats(start):
    while True:
        await asyncio.sleep(2)
        async with lock:
            c = counter
        el = time.time() - start
        print(f"[{el:8.1f}s] req={c} rps={c/el:8.1f}", flush=True)

async def main():
    p = argparse.ArgumentParser()
    p.add_argument("-u", "--url", required=True)
    p.add_argument("-c", "--concurrency", type=int, default=500)
    p.add_argument("-t", "--timeout", type=float, default=5.0)
    p.add_argument("--proxy-file", default=None)
    a = p.parse_args()

    proxies = [None]
    if a.proxy_file:
        proxies = load_lines(a.proxy_file) or [None]

    sem = asyncio.Semaphore(a.concurrency)
    start = time.time()
    asyncio.create_task(stats(start))
    await asyncio.gather(*[
        asyncio.create_task(worker(a.url, random.choice(proxies), sem, a.timeout))
        for _ in range(a.concurrency)
    ])

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass