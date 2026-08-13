"""
SCELE Notifier - Fase 1 (login-based)
RSS gak tersedia di SCELE, jadi login pake akun sendiri (requests.Session()),
lalu scrape halaman forum diskusi & Dashboard Timeline. Kalau ada yang baru,
kirim notifikasi Telegram.

Cara pake:
1. pip install -r requirements.txt
2. Isi .env (lihat .env.example) dengan username/password SCELE,
   link forum yang mau dipantau, Bot Token, dan Chat ID
3. python forum_notifier.py
"""

import os
import re
import time
import json
import html
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://scele.cs.ui.ac.id"
LOGIN_URL = f"{BASE_URL}/login/index.php"
DASHBOARD_URL = f"{BASE_URL}/my/"
AJAX_URL = f"{BASE_URL}/lib/ajax/service.php"
SEEN_FILE = "seen_posts.json"
DEBUG_HTML_DIR = "debug_html"


def load_seen() -> set:
    """Baca daftar post/deadline yang udah pernah dikirim sebelumnya."""
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_seen(seen: set) -> None:
    """Simpen daftar yang udah dikirim, biar gak dikirim ulang."""
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)


def save_debug_html(name: str, html: str) -> None:
    """Simpen HTML mentah hasil fetch, buat verifikasi manual selector.
    Cuma aktif kalau env DEBUG_SAVE_HTML=1, biar gak numpuk file pas
    jalan otomatis di GitHub Actions.
    """
    if os.environ.get("DEBUG_SAVE_HTML") != "1":
        return
    os.makedirs(DEBUG_HTML_DIR, exist_ok=True)
    with open(os.path.join(DEBUG_HTML_DIR, name), "w", encoding="utf-8") as f:
        f.write(html)


def send_telegram(token: str, chat_id: str, message: str) -> None:
    """Kirim pesan ke Telegram lewat Bot API."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(url, data={"chat_id": chat_id, "text": message})
    if not resp.ok:
        print(f"Gagal kirim Telegram: {resp.status_code} {resp.text}")


def scele_login(session: requests.Session, username: str, password: str) -> None:
    """Login ke SCELE (Moodle) pake session yang sama buat request selanjutnya.

    Moodle wajibin 'logintoken' (CSRF token) yang cuma valid buat session
    cookie yang sama saat token itu diambil. Makanya harus GET halaman
    login dulu (biar dapet cookie + token), baru POST -- gak bisa langsung
    tembak POST dengan token sembarangan.
    """
    login_page = session.get(LOGIN_URL, timeout=15)
    login_page.raise_for_status()

    soup = BeautifulSoup(login_page.text, "html.parser")
    token_input = soup.find("input", {"name": "logintoken"})
    if token_input is None:
        raise RuntimeError(
            "Gak nemu logintoken di halaman login. Kemungkinan struktur "
            "SCELE berubah -- cek debug_html/login_page.html."
        )

    resp = session.post(
        LOGIN_URL,
        data={
            "username": username,
            "password": password,
            "logintoken": token_input["value"],
        },
        timeout=15,
    )
    resp.raise_for_status()
    save_debug_html("after_login.html", resp.text)

    if "/login/index.php" in resp.url:
        error_soup = BeautifulSoup(resp.text, "html.parser")
        error_el = error_soup.find(class_="loginerrors") or error_soup.find(
            id="loginerrormessage"
        )
        reason = error_el.get_text(strip=True) if error_el else "alasan tidak diketahui"
        raise RuntimeError(f"Login SCELE gagal: {reason}")

    print("Login SCELE berhasil.")


def extract_query_id(url: str) -> str:
    match = re.search(r"[?&]id=(\d+)", url)
    return match.group(1) if match else "unknown"


def fetch_forum_entries(session: requests.Session, forum_url: str, seen: set) -> list:
    """Ambil diskusi baru dari satu halaman forum (mod/forum/view.php?id=...)."""
    resp = session.get(forum_url, timeout=15)
    resp.raise_for_status()
    save_debug_html(f"forum_{extract_query_id(forum_url)}.html", resp.text)

    soup = BeautifulSoup(resp.text, "html.parser")
    new_entries = []
    for link in soup.select("a[href*='discuss.php']"):
        href = urljoin(BASE_URL, link.get("href", ""))
        match = re.search(r"[?&]d=(\d+)", href)
        title = link.get_text(strip=True)
        if not match or not title:
            continue

        entry_id = f"forum:{match.group(1)}"
        if entry_id in seen:
            continue

        new_entries.append({"id": entry_id, "title": html.unescape(title), "link": href})
        seen.add(entry_id)

    return new_entries


def get_sesskey(session: requests.Session) -> str:
    """Ambil sesskey (token internal Moodle) dari halaman Dashboard.
    Dipake buat manggil endpoint AJAX Moodle langsung.
    """
    resp = session.get(DASHBOARD_URL, timeout=15)
    resp.raise_for_status()
    save_debug_html("dashboard.html", resp.text)

    soup = BeautifulSoup(resp.text, "html.parser")
    sesskey_input = soup.find("input", {"name": "sesskey"})
    if sesskey_input is None:
        raise RuntimeError("Gak nemu sesskey di Dashboard -- cek debug_html/dashboard.html.")
    return sesskey_input["value"]


def fetch_timeline_entries(session: requests.Session, seen: set) -> list:
    """Ambil deadline baru dari widget Timeline di Dashboard.

    Timeline di SCELE ke-render lewat JavaScript, bukan HTML statis --
    udah dicek manual: elemen buat nampung event-nya selalu kosong pas
    di-fetch pake requests. Makanya di sini kita manggil endpoint AJAX
    internal Moodle-nya langsung (core_calendar_get_action_events_by_timesort),
    yang malah lebih stabil daripada scrape HTML karena hasilnya JSON
    terstruktur (gak gampang rusak kalau tema SCELE berubah).
    """
    sesskey = get_sesskey(session)

    today_midnight = int(time.time()) - (int(time.time()) % 86400)
    payload = [{
        "index": 0,
        "methodname": "core_calendar_get_action_events_by_timesort",
        "args": {
            "limitnum": 50,
            "timesortfrom": today_midnight,
            "limittononsuspendedevents": True,
        },
    }]

    resp = session.post(
        AJAX_URL,
        params={"sesskey": sesskey, "info": "core_calendar_get_action_events_by_timesort"},
        json=payload,
        timeout=15,
    )
    resp.raise_for_status()
    result = resp.json()[0]

    if result.get("error"):
        raise RuntimeError(f"AJAX Timeline error: {result.get('exception')}")

    new_entries = []
    for event in result["data"]["events"]:
        entry_id = f"timeline:{event['id']}"
        if entry_id in seen:
            continue

        link = (event.get("action") or {}).get("url") or event.get("url", DASHBOARD_URL)
        title = html.unescape(f"{event['name']} ({event['course']['fullname']})")

        new_entries.append({"id": entry_id, "title": title, "link": link})
        seen.add(entry_id)

    return new_entries


def main():
    username = os.environ["SCELE_USERNAME"]
    password = os.environ["SCELE_PASSWORD"]
    bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    forum_urls = [
        u.strip() for u in os.environ.get("SCELE_FORUM_URLS", "").split(",") if u.strip()
    ]

    seen = load_seen()
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (SCELE Notifier Bot)"})

    scele_login(session, username, password)

    all_new = []

    if not forum_urls:
        print("SCELE_FORUM_URLS kosong, skip cek forum.")
    for forum_url in forum_urls:
        try:
            all_new.extend(fetch_forum_entries(session, forum_url, seen))
        except Exception as e:
            print(f"Gagal cek forum {forum_url}: {e}")

    try:
        all_new.extend(fetch_timeline_entries(session, seen))
    except Exception as e:
        print(f"Gagal cek timeline: {e}")

    for entry in all_new:
        sumber = "Forum" if entry["id"].startswith("forum:") else "Timeline"
        message = f"[{sumber}] {entry['title']}\n{entry['link']}"
        send_telegram(bot_token, chat_id, message)
        print(f"Notified: {entry['title']}")

    save_seen(seen)

    if not all_new:
        print("Gak ada yang baru.")


if __name__ == "__main__":
    main()
