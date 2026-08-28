import httpx
import ssl
import time
import random
import threading
import os
import sys
import binascii
import concurrent.futures
from urllib.parse import urlencode
import requests
import SignerPy

HOSTS = [
    "api.tiktokv.us",
    "api16-normal-useast5.tiktokv.us",
    "api16-normal-useast8.tiktokv.us",
    "api19-normal-useast5.tiktokv.us",
    "api19-normal-useast8.tiktokv.us",
]

CIPHERS = [
    'ECDHE-ECDSA-AES128-GCM-SHA256', 'ECDHE-RSA-AES128-GCM-SHA256',
    'ECDHE-ECDSA-AES256-GCM-SHA384', 'ECDHE-RSA-AES256-GCM-SHA384',
    'ECDHE-ECDSA-CHACHA20-POLY1305', 'ECDHE-RSA-CHACHA20-POLY1305',
    'DHE-RSA-AES128-GCM-SHA256', 'DHE-RSA-AES256-GCM-SHA384',
    'AES128-GCM-SHA256', 'AES256-GCM-SHA384',
    'AES128-SHA256', 'AES256-SHA256', 'AES128-SHA', 'AES256-SHA',
]


class RateLimiter:
    def __init__(self, max_per_sec):
        self.max_per_sec = max_per_sec
        self.tokens = max_per_sec
        self.lock = threading.Lock()
        self.last_refill = time.monotonic()
        self.event = threading.Event()
        self.event.set()

    def acquire(self):
        while True:
            with self.lock:
                now = time.monotonic()
                elapsed = now - self.last_refill
                if elapsed >= 1.0:
                    self.tokens = self.max_per_sec
                    self.last_refill = now
                if self.tokens > 0:
                    self.tokens -= 1
                    return
                self.event.clear()
            self.event.wait(timeout=0.01)


class Stats:
    def __init__(self):
        self.hits = 0
        self.bads = 0
        self.retried = 0
        self.checked = 0
        self.skipped = 0
        self.lock = threading.Lock()

    def inc_hit(self):
        with self.lock:
            self.hits += 1
            self.checked += 1

    def inc_bad(self):
        with self.lock:
            self.bads += 1
            self.checked += 1

    def inc_retry(self):
        with self.lock:
            self.retried += 1
            self.checked += 1

    def inc_skip(self):
        with self.lock:
            self.skipped += 1
            self.checked += 1

    def snapshot(self):
        with self.lock:
            return self.hits, self.bads, self.retried, self.checked, self.skipped


def enable_vt100():
    if os.name != 'nt':
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass


def build_ssl_context():
    try:
        ciphers = CIPHERS[:]
        random.shuffle(ciphers)
        ctx = ssl.create_default_context()
        ctx.set_ciphers(':'.join(ciphers))
        ctx.options |= ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.maximum_version = ssl.TLSVersion.TLSv1_3
        return ctx
    except Exception:
        return None


def load_lines(filepath):
    if not os.path.isfile(filepath):
        print(f"[!] File not found: {filepath}")
        sys.exit(1)
    with open(filepath, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def load_config():
    config = {}
    if os.path.isfile("config.txt"):
        with open("config.txt", 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    config[k.strip()] = v.strip()
    return config


def check_username(username, client):
    for attempt in range(3):
        try:
            host = random.choice(HOSTS)
            params = {
                "passport-sdk-version": "19",
                "iid": str(random.randint(10**18, 10**19 - 1)),
                "device_id": str(random.randint(10**18, 10**19 - 1)),
                "aid": "1233",
                "device_type": "SM-A156E",
                "os_version": "15",
                "language": "en",
                "region": "US",
                "version_name": "31.5.3",
                "version_code": "310503",
                "app_name": "musical_ly",
                "device_platform": "android",
                "os": "android",
                "openudid": binascii.hexlify(os.urandom(8)).decode(),
                "ac": "wifi",
                "channel": "googleplay",
                "os_api": "35",
                "sys_region": "US",
                "timezone_name": "Asia/Muscat",
                "carrier_region": "US",
                "build_number": "31.5.3",
                "locale": "en",
                "ts": str(int(time.time())),
            }
            data = {
                "login_name": username,
                "account_sdk_source": "app",
                "multi_login": "1",
            }
            headers = SignerPy.sign(
                params=urlencode(params),
                payload=urlencode(data),
                version=8404,
                aid=1233,
            )
            headers.update({
                "User-Agent": "com.zhiliaoapp.musically/2023105030 (Linux; U; Android 15; en_US; SM-A156E; Build/V417IR;tt-ok/3.12.13.4-tiktok)",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "sdk-version": "2",
                "passport-sdk-version": "19",
            })

            url = f"https://{host}/passport/login_name/check/"
            resp = client.post(url, params=params, headers=headers, data=data)

            if "login_name" in resp.text:
                return "hit"
            elif "1024" in resp.text:
                return "unavailable"
            elif "Maximum number of attempts reached" in resp.text:
                if attempt == 2:
                    return "limited"
                continue
            else:
                return "unknown"

        except Exception:
            if attempt == 2:
                return "error"
            continue
    return "error"


def send_telegram(username, token, chat_id):
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            params={"chat_id": chat_id, "text": f"Good : `{username}`", "parse_mode": "Markdown"},
            timeout=10,
        )
    except Exception:
        pass


def worker(user_slice, proxy, stats, glitch_set, hit_lock, rate_limiter, tg_token, tg_chat_id):
    ctx = build_ssl_context()
    client = httpx.Client(http2=False, verify=ctx, timeout=5.0, proxy=f"http://{proxy}")

    for username in user_slice:
        if username in glitch_set:
            stats.inc_skip()
            continue

        rate_limiter.acquire()

        result = check_username(username, client)

        if result == "hit":
            stats.inc_hit()
            send_telegram(username, tg_token, tg_chat_id)
            with hit_lock:
                with open('good.txt', 'a', encoding='utf-8') as f:
                    f.write(username + '\n')
        elif result == "unavailable":
            stats.inc_bad()
        elif result == "limited":
            stats.inc_retry()
        else:
            stats.inc_bad()

    client.close()


def display_stats(stats, total_users, active_flag):
    enable_vt100()
    sys.stdout.write('\033[2J')
    sys.stdout.flush()
    last = time.time()

    while active_flag.is_set():
        now = time.time()
        if now - last < 0.3:
            time.sleep(0.05)
            continue
        last = now

        h, b, r, c, s = stats.snapshot()
        pct = (c / total_users * 100) if total_users > 0 else 0
        output = (
            f"\r━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"  TikTok Username Checker\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"  Hits    : {h}\n"
            f"  Bads    : {b}\n"
            f"  Retried : {r}\n"
            f"  Skipped : {s}\n"
            f"  Checked : {c} / {total_users} ({pct:.1f}%)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"  Programmer : @umw_m\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )
        sys.stdout.write(f'\033[H{output}')
        sys.stdout.flush()

    h, b, r, c, s = stats.snapshot()
    sys.stdout.write(
        f'\033[H'
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"  TikTok Username Checker\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"  Hits    : {h}\n"
        f"  Bads    : {b}\n"
        f"  Retried : {r}\n"
        f"  Skipped : {s}\n"
        f"  Checked : {c} / {total_users} (100.0%)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"  [+] DONE!\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )
    sys.stdout.flush()


def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    enable_vt100()

    config = load_config()
    TG_TOKEN = config.get("TG_TOKEN", "")
    TG_CHAT_ID = config.get("TG_CHAT_ID", "")
    proxies = load_lines("proxy.txt")
    users = load_lines("users.txt")
    RATE_LIMIT = int(config.get("RATE_LIMIT", "200"))
    THREADS_PER_PROXY = int(config.get("THREADS_PER_PROXY", "100"))

    glitch_set = set()
    if os.path.isfile("glitch.txt"):
        with open("glitch.txt", "r", encoding="utf-8") as f:
            glitch_set = {line.strip() for line in f if line.strip()}

    total_threads = len(proxies) * THREADS_PER_PROXY
    chunk_size = len(users) // total_threads
    remainder = len(users) % total_threads

    print(f"[*] Loaded {len(proxies)} proxies")
    print(f"[*] Loaded {len(users)} users")
    print(f"[*] Loaded {len(glitch_set)} glitch entries")
    print(f"[*] Rate limit per proxy: {RATE_LIMIT} req/s")
    print(f"[*] Threads per proxy: {THREADS_PER_PROXY}")
    print(f"[*] Total threads: {total_threads}")

    stats = Stats()
    active_flag = threading.Event()
    active_flag.set()
    hit_lock = threading.Lock()

    display_thread = threading.Thread(
        target=display_stats,
        args=(stats, len(users), active_flag),
        daemon=True,
    )
    display_thread.start()

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=total_threads)
    futures = []
    idx = 0
    for proxy in proxies:
        limiter = RateLimiter(RATE_LIMIT)
        for _ in range(THREADS_PER_PROXY):
            extra = 1 if idx < remainder else 0
            end = idx + chunk_size + extra
            user_slice = users[idx:end]
            idx = end
            f = executor.submit(worker, user_slice, proxy, stats, glitch_set, hit_lock, limiter, TG_TOKEN, TG_CHAT_ID)
            futures.append(f)

    for f in concurrent.futures.as_completed(futures):
        pass

    active_flag.clear()
    executor.shutdown(wait=False)

    print(f"\n[+] Done! Hits: {stats.hits} | Bads: {stats.bads} | Skipped: {stats.skipped}")


if __name__ == "__main__":
    main()
