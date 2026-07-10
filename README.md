# Spotify Remote Bot untuk Telegram

Bot Telegram untuk **mengontrol pemutaran musik** di akun Spotify Premium kamu
(play, pause, skip, atur volume, pilih playlist) lewat Spotify Web API resmi,
lengkap dengan sistem **role admin**.

> ⚠️ **Catatan penting**: Bot ini TIDAK mengunduh file MP3/audio dari Spotify.
> Spotify API memang tidak menyediakan fitur unduh — bot ini hanya
> mengendalikan aplikasi Spotify yang sudah berjalan di perangkatmu
> (HP, laptop, speaker, dsb), sama seperti "remote control" resmi.
>
> Soal fitur "online status": Telegram Bot API tidak mengizinkan bot melihat
> status online asli user lain (dibatasi demi privasi). Yang bisa dilacak
> bot ini adalah "terakhir aktif menggunakan bot" (last seen di dalam bot),
> bisa dilihat admin lewat `/listusers`.

## Fitur

**Kontrol Spotify** (semua user yang diizinkan):
- `/nowplaying` — lihat lagu yang sedang diputar
- `/play [judul lagu]` — lanjutkan pemutaran, atau cari & putar lagu tertentu
- `/pause`, `/next`, `/prev`
- `/volume <0-100>`
- `/devices` — daftar perangkat Spotify yang aktif
- `/setdevice <nomor>` — pindah pemutaran ke perangkat lain
- `/playlists` — daftar playlist kamu
- `/playpl <nomor>` — putar salah satu playlist

**Admin only**:
- `/adduser <telegram_id>` — izinkan user baru pakai bot
- `/removeuser <telegram_id>` — cabut akses user
- `/listusers` — lihat semua admin & user, plus waktu terakhir aktif
- `/broadcast <pesan>` — kirim pengumuman ke semua user

## Setup

### 1. Buat Bot Telegram
1. Chat ke [@BotFather](https://t.me/BotFather) di Telegram
2. Kirim `/newbot`, ikuti instruksinya
3. Salin **token** yang diberikan

### 2. Buat Aplikasi Spotify
1. Buka [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Klik **Create app**
3. Isi nama & deskripsi bebas
4. Di kolom **Redirect URI**, isi: `http://127.0.0.1:8888/callback`
   (harus sama persis dengan yang di file `.env` nanti)
5. Setelah dibuat, salin **Client ID** dan **Client Secret**
6. Pastikan akun Spotify kamu berstatus **Premium** — kontrol playback
   (play/pause/skip/volume) lewat API hanya berfungsi untuk akun Premium

### 3. Cari User ID Telegram kamu
Chat ke [@userinfobot](https://t.me/userinfobot), dia akan membalas ID kamu.

### 4. Install & Konfigurasi
```bash
# Masuk ke folder project
cd spotify_telegram_bot

# (opsional tapi disarankan) buat virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Salin file environment lalu isi datanya
cp .env.example .env
```

Buka `.env` dan isi:
```
TELEGRAM_BOT_TOKEN=token_dari_botfather
ADMIN_IDS=id_telegram_kamu
SPOTIFY_CLIENT_ID=client_id_dari_dashboard
SPOTIFY_CLIENT_SECRET=client_secret_dari_dashboard
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

Bisa isi lebih dari satu admin, pisahkan dengan koma:
`ADMIN_IDS=111111,222222`

### 5. Login Spotify (sekali di awal)
Jalankan Python singkat ini sekali saja di komputer yang sama untuk
membuat token cache (`spotipy` akan membuka alur OAuth):

```bash
python3 -c "from dotenv import load_dotenv; load_dotenv(); import spotify_client as sp; print(sp.get_client().current_user())"
```

Ikuti link yang muncul di terminal, login ke Spotify, izinkan akses,
lalu **salin URL hasil redirect** dan tempel balik ke terminal saat diminta.
Setelah ini token tersimpan otomatis di file `.spotify_token_cache`
(otomatis diperbarui, tidak perlu login ulang selama bot jalan terus-terusan).

### 6. Jalankan Bot
```bash
python3 bot.py
```

Buka Telegram, chat bot kamu, kirim `/start`.

## Menambahkan user lain

Sebagai admin, kirim:
```
/adduser 123456789
```
(ganti dengan Telegram ID orang yang ingin diizinkan)

## Menjalankan terus-menerus (opsional)

Untuk dijalankan 24/7, gunakan salah satu:
- **VPS/server**: pakai `systemd`, `pm2`, atau `tmux`/`screen`
- **Docker**: buat `Dockerfile` sederhana dari `requirements.txt`
- Pastikan Spotify tetap terbuka di minimal satu perangkat agar ada
  "device" aktif yang bisa dikontrol

## Batasan yang perlu diketahui

- Kontrol playback (play/pause/skip/volume) via Spotify API **hanya untuk
  akun Premium** — akun gratis tidak didukung Spotify untuk fitur ini.
- Bot tidak bisa mengunduh audio — ini murni remote control resmi.
- Status "online" yang ditampilkan bot adalah aktivitas terakhir di dalam
  bot (last seen), bukan status online Telegram asli (dibatasi Telegram
  Bot API untuk alasan privasi).
