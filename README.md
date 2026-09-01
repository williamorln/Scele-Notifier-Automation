# SCELE Notifier (Fase 1)

Bot sederhana: login ke SCELE (Moodle) pake akun sendiri, cek forum diskusi
dan Dashboard Timeline, kirim notif Telegram kalau ada post/deadline baru.

RSS forum gak tersedia di instance SCELE ini (dimatiin di level admin), jadi
Fase 1 ini sekalian gabungin dua sumber yang tadinya direncanain kepisah
(forum di Fase 1, Timeline di Fase 2) lewat satu metode: login session.

## Setup

1. **Bikin Telegram Bot**
   - Chat ke [@BotFather](https://t.me/BotFather) di Telegram
   - Ketik `/newbot`, ikutin instruksinya
   - Simpen **Bot Token** yang dikasih

2. **Dapetin Chat ID lo**
   - Chat ke [@userinfobot](https://t.me/userinfobot)
   - Dia bakal balikin Chat ID lo

3. **Cari link forum yang mau dipantau (opsional)**
   - Login ke SCELE, masuk ke course-nya, buka forum yang mau dipantau
   - Copy link halaman forum-nya, bentuknya `.../mod/forum/view.php?id=XXXXX`
   - Boleh lebih dari satu, nanti dipisah koma di `.env`
   - Boleh dikosongin kalau cuma mau pantau Timeline dulu

4. **Setup lokal buat testing**
   ```bash
   pip install -r requirements.txt
   cp .env.example .env
   # isi .env: SCELE_USERNAME, SCELE_PASSWORD, SCELE_FORUM_URLS (opsional),
   # TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
   ```
   Jalanin manual dulu buat mastiin gak error:
   ```bash
   python forum_notifier.py
   ```
   (Script otomatis baca `.env` lewat `python-dotenv`, gak perlu `export`/`source` manual lagi.)

   Set `DEBUG_SAVE_HTML=1` di `.env` kalau mau nyimpen HTML mentah hasil
   fetch ke folder `debug_html/` (berguna buat ngecek kalau scraping gak
   nemu apa-apa padahal harusnya ada).

5. **Setup GitHub Actions (biar jalan otomatis, gratis)**
   - Push project ini ke repo GitHub
   - `check-forum.yml` udah ada di `.github/workflows/check-forum.yml`
   - Di repo, masuk **Settings > Secrets and variables > Actions**, tambahin 5 secret:
     `SCELE_USERNAME`, `SCELE_PASSWORD`, `SCELE_FORUM_URLS`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
   - Selesai, bot bakal jalan otomatis tiap 4 jam

   **Catatan risiko:** ini nyimpen password akun SCELE lo sebagai GitHub
   secret dan dipake login otomatis tiap 4 jam dari server GitHub (bukan dari
   device lo). Secret di GitHub Actions terenkripsi dan gak pernah keliatan
   di kode meski repo-nya public, tapi kalau akun GitHub lo sendiri
   kecompromise (misal password GitHub lo bocor), penyerang bisa buka
   Settings > Secrets dan re-set workflow buat nge-leak nilai secret itu.
   Jaga akun GitHub lo (aktifin 2FA) sama kayak lo jaga password SCELE.

## Operasional

- **Testing manual (lokal):** pastiin `venv` aktif, lalu `python forum_notifier.py`.
  Cek output di terminal + `seen_posts.json` (isinya nambah tiap ada entry baru).
- **Jalanin manual di GitHub Actions** (gak perlu nunggu jadwal jam-an):
  tab **Actions** > pilih workflow **Check SCELE Forum** > tombol **Run workflow**.
- **Liat log run yang udah lewat / debug kalau gagal:** tab **Actions** > klik
  run yang mau dicek > klik job **check** > expand step yang error.
- **Update link forum yang dipantau:** edit `.env` (lokal) dan/atau secret
  `SCELE_FORUM_URLS` di GitHub (Settings > Secrets and variables > Actions >
  edit `SCELE_FORUM_URLS`).
- **Berhentiin sementara:** tab **Actions** > pilih workflow **Check SCELE
  Forum** > menu **...** > **Disable workflow**.

## Struktur file

```
forum_notifier.py                  -> logic utama (login, scrape, notif)
requirements.txt                   -> dependencies
.env.example                       -> template config (jangan commit .env asli)
.github/workflows/check-forum.yml  -> workflow GitHub Actions
seen_posts.json                    -> otomatis dibikin script, nyimpen post/event yang udah dinotif
debug_html/                        -> opsional, HTML mentah buat debug (gitignored)
```
