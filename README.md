# SCELE Forum Notifier (Fase 1)

Bot sederhana: cek RSS forum SCELE, kirim notif Telegram kalau ada post baru.
Ini baru forum doang (Fase 1). Timeline/assignment nyusul di Fase 2.

## Setup

1. **Bikin Telegram Bot**
   - Chat ke [@BotFather](https://t.me/BotFather) di Telegram
   - Ketik `/newbot`, ikutin instruksinya
   - Simpen **Bot Token** yang dikasih

2. **Dapetin Chat ID lo**
   - Chat ke [@userinfobot](https://t.me/userinfobot)
   - Dia bakal balikin Chat ID lo

3. **Ambil link RSS forum SCELE**
   - Login ke SCELE
   - Masuk ke forum yang mau dipantau
   - Cari opsi RSS/subscribe (biasanya ada icon RSS di halaman forum, atau di Preferences > RSS)
   - Copy link-nya (link ini udah termasuk token pribadi lo, jangan disebar)

4. **Setup lokal buat testing**
   ```bash
   pip install -r requirements.txt
   cp .env.example .env
   # isi .env dengan 3 nilai di atas
   ```
   Jalanin manual dulu buat mastiin gak error:
   ```bash
   export $(cat .env | xargs) && python forum_notifier.py
   ```

5. **Setup GitHub Actions (biar jalan otomatis, gratis)**
   - Push project ini ke repo GitHub baru
   - Pindahin `check-forum.yml` ke folder `.github/workflows/check-forum.yml`
   - Di repo, masuk **Settings > Secrets and variables > Actions**, tambahin 3 secret:
     `SCELE_RSS_URL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
   - Selesai, bot bakal jalan otomatis tiap 30 menit

## Struktur file

```
forum_notifier.py    -> logic utama
requirements.txt     -> dependencies
.env.example          -> template config (jangan commit .env asli)
check-forum.yml       -> workflow GitHub Actions (pindahin ke .github/workflows/)
seen_posts.json       -> otomatis dibikin script, nyimpen post yang udah dinotif
```
