"""
Bot Telegram - Remote Control Spotify + Sistem Admin
=====================================================
Bot ini mengontrol pemutaran musik di akun Spotify Premium kamu lewat
Spotify Web API resmi (play/pause/next/prev/volume/playlist).
Bot ini TIDAK mengunduh file audio dari mana pun.

Jalankan: python bot.py
"""
import logging
import os
from functools import wraps

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import spotify_client as sp
import user_store as store

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def require_allowed(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *a, **kw):
        user = update.effective_user
        if not store.is_allowed(user.id):
            await update.message.reply_text(
                "⛔ Kamu belum diizinkan pakai bot ini. Minta admin menambahkanmu dengan /adduser."
            )
            return
        store.touch_last_seen(user.id, user.full_name)
        return await func(update, context, *a, **kw)
    return wrapper


def require_admin(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *a, **kw):
        user = update.effective_user
        if not store.is_admin(user.id):
            await update.message.reply_text("⛔ Perintah ini khusus admin.")
            return
        store.touch_last_seen(user.id, user.full_name)
        return await func(update, context, *a, **kw)
    return wrapper


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if store.is_admin(user.id):
        role = "Admin 👑"
    elif store.is_allowed(user.id):
        role = "User ✅"
    else:
        role = "Belum diizinkan ⛔"

    await update.message.reply_text(
        f"🎵 *Spotify Remote Bot*\n\n"
        f"Halo {user.first_name}! Status kamu: {role}\n\n"
        f"Perintah pemutaran:\n"
        f"/nowplaying - lagu yang sedang diputar\n"
        f"/play [judul lagu] - lanjut main / cari & putar lagu\n"
        f"/pause - jeda\n"
        f"/next - lagu berikutnya\n"
        f"/prev - lagu sebelumnya\n"
        f"/volume <0-100> - atur volume\n"
        f"/devices - daftar perangkat\n"
        f"/setdevice <nomor> - pindah perangkat aktif\n"
        f"/playlists - daftar playlist kamu\n"
        f"/playpl <nomor> - putar playlist\n",
        parse_mode="Markdown",
    )


@require_allowed
async def now_playing_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info = sp.now_playing()
    if not info:
        await update.message.reply_text("Tidak ada yang sedang diputar saat ini.")
        return
    progress = info["progress_ms"] // 1000
    duration = info["duration_ms"] // 1000
    status = "▶️ Playing" if info["is_playing"] else "⏸️ Paused"
    await update.message.reply_text(
        f"{status}\n\n"
        f"🎵 {info['name']}\n"
        f"👤 {info['artists']}\n"
        f"💿 {info['album']}\n"
        f"📱 {info['device']}\n"
        f"⏱️ {progress//60}:{progress%60:02d} / {duration//60}:{duration%60:02d}\n"
        f"{info['url']}"
    )


@require_allowed
async def play_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args) if context.args else None
    try:
        if query:
            track = sp.search_and_play(query)
            if track:
                await update.message.reply_text(f"▶️ Memutar: {track}")
            else:
                await update.message.reply_text("Lagu tidak ditemukan.")
        else:
            sp.play()
            await update.message.reply_text("▶️ Melanjutkan pemutaran.")
    except Exception as e:
        await update.message.reply_text(f"Gagal memutar. Pastikan ada perangkat Spotify aktif.\n({e})")


@require_allowed
async def pause_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        sp.pause()
        await update.message.reply_text("⏸️ Dijeda.")
    except Exception as e:
        await update.message.reply_text(f"Gagal jeda.\n({e})")


@require_allowed
async def next_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        sp.next_track()
        await update.message.reply_text("⏭️ Lagu berikutnya.")
    except Exception as e:
        await update.message.reply_text(f"Gagal skip.\n({e})")


@require_allowed
async def prev_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        sp.previous_track()
        await update.message.reply_text("⏮️ Lagu sebelumnya.")
    except Exception as e:
        await update.message.reply_text(f"Gagal kembali.\n({e})")


@require_allowed
async def volume_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Pakai format: /volume 50")
        return
    try:
        sp.set_volume(int(context.args[0]))
        await update.message.reply_text(f"🔊 Volume diatur ke {context.args[0]}%.")
    except Exception as e:
        await update.message.reply_text(f"Gagal atur volume.\n({e})")


@require_allowed
async def devices_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    devices = sp.list_devices()
    if not devices:
        await update.message.reply_text("Tidak ada perangkat aktif. Buka Spotify di HP/laptop dulu.")
        return
    context.user_data["devices"] = devices
    lines = [
        f"{i+1}. {d['name']} ({d['type']}){' — aktif' if d['is_active'] else ''}"
        for i, d in enumerate(devices)
    ]
    await update.message.reply_text(
        "📱 Perangkat tersedia:\n" + "\n".join(lines) + "\n\nPakai /setdevice <nomor> untuk pindah."
    )


@require_allowed
async def setdevice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    devices = context.user_data.get("devices")
    if not devices:
        await update.message.reply_text("Jalankan /devices dulu untuk lihat daftarnya.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Pakai format: /setdevice 1")
        return
    idx = int(context.args[0]) - 1
    if idx < 0 or idx >= len(devices):
        await update.message.reply_text("Nomor tidak valid.")
        return
    sp.set_active_device(devices[idx]["id"])
    await update.message.reply_text(f"✅ Pindah ke perangkat: {devices[idx]['name']}")


@require_allowed
async def playlists_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    playlists = sp.list_playlists()
    if not playlists:
        await update.message.reply_text("Tidak ada playlist ditemukan.")
        return
    context.user_data["playlists"] = playlists
    lines = [f"{i+1}. {p['name']} ({p['tracks']} lagu)" for i, p in enumerate(playlists)]
    await update.message.reply_text(
        "🎶 Playlist kamu:\n" + "\n".join(lines) + "\n\nPakai /playpl <nomor> untuk memutar."
    )


@require_allowed
async def playpl_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    playlists = context.user_data.get("playlists")
    if not playlists:
        await update.message.reply_text("Jalankan /playlists dulu untuk lihat daftarnya.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Pakai format: /playpl 1")
        return
    idx = int(context.args[0]) - 1
    if idx < 0 or idx >= len(playlists):
        await update.message.reply_text("Nomor tidak valid.")
        return
    try:
        sp.play_playlist(playlists[idx]["id"])
        await update.message.reply_text(f"▶️ Memutar playlist: {playlists[idx]['name']}")
    except Exception as e:
        await update.message.reply_text(f"Gagal memutar playlist.\n({e})")


@require_admin
async def adduser_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Pakai format: /adduser <user_id_telegram>")
        return
    uid = int(context.args[0])
    store.add_allowed_user(uid)
    await update.message.reply_text(f"✅ User {uid} sekarang boleh pakai bot.")


@require_admin
async def removeuser_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Pakai format: /removeuser <user_id_telegram>")
        return
    uid = int(context.args[0])
    if store.remove_allowed_user(uid):
        await update.message.reply_text(f"✅ User {uid} dihapus dari daftar akses.")
    else:
        await update.message.reply_text("User tidak ditemukan di daftar.")


@require_admin
async def listusers_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    allowed = store.list_allowed_users()
    admins = store.get_admin_ids()
    last_seen = store.get_last_seen()

    lines = ["👑 Admin:"]
    lines += [f"  - {a}" for a in admins] or ["  (tidak ada)"]
    lines.append("\n✅ User diizinkan:")
    if not allowed:
        lines.append("  (tidak ada)")
    for uid, info in allowed.items():
        seen = last_seen.get(uid, {}).get("time", "belum pernah")
        lines.append(f"  - {uid} ({info.get('name','?')}) — terakhir aktif: {seen}")

    await update.message.reply_text("\n".join(lines))


@require_admin
async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Pakai format: /broadcast <pesan>")
        return
    message = " ".join(context.args)
    allowed = store.list_allowed_users()
    admins = store.get_admin_ids()
    targets = set(int(k) for k in allowed.keys()) | admins

    sent = 0
    for uid in targets:
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 {message}")
            sent += 1
        except Exception:
            pass
    await update.message.reply_text(f"Broadcast terkirim ke {sent} user.")


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN belum diset di .env")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("nowplaying", now_playing_cmd))
    app.add_handler(CommandHandler("play", play_cmd))
    app.add_handler(CommandHandler("pause", pause_cmd))
    app.add_handler(CommandHandler("next", next_cmd))
    app.add_handler(CommandHandler("prev", prev_cmd))
    app.add_handler(CommandHandler("volume", volume_cmd))
    app.add_handler(CommandHandler("devices", devices_cmd))
    app.add_handler(CommandHandler("setdevice", setdevice_cmd))
    app.add_handler(CommandHandler("playlists", playlists_cmd))
    app.add_handler(CommandHandler("playpl", playpl_cmd))

    app.add_handler(CommandHandler("adduser", adduser_cmd))
    app.add_handler(CommandHandler("removeuser", removeuser_cmd))
    app.add_handler(CommandHandler("listusers", listusers_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))

    logger.info("Bot berjalan...")
    app.run_polling()


if __name__ == "__main__":
    main()
