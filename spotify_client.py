"""
Wrapper untuk Spotify Web API (spotipy).
Bot ini HANYA mengontrol pemutaran resmi lewat akun Spotify Premium kamu
(play/pause/skip/volume/lihat playlist) - tidak mengunduh audio apapun,
karena Spotify API memang tidak menyediakan endpoint untuk itu.
"""
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

SCOPE = (
    "user-read-playback-state "
    "user-modify-playback-state "
    "user-read-currently-playing "
    "playlist-read-private "
    "playlist-read-collaborative"
)

_sp = None


def _build_auth_manager():
    return SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
        scope=SCOPE,
        cache_path=".spotify_token_cache",
        open_browser=False,
    )


def get_client():
    global _sp
    if _sp is None:
        _sp = spotipy.Spotify(auth_manager=_build_auth_manager())
    return _sp


def get_auth_url() -> str:
    return _build_auth_manager().get_authorize_url()


def complete_auth(redirected_url_or_code: str) -> None:
    auth_manager = _build_auth_manager()
    code = auth_manager.parse_response_code(redirected_url_or_code)
    auth_manager.get_access_token(code, as_dict=False)


def now_playing():
    sp = get_client()
    current = sp.current_playback()
    if not current or not current.get("item"):
        return None
    item = current["item"]
    return {
        "name": item["name"],
        "artists": ", ".join(a["name"] for a in item["artists"]),
        "album": item["album"]["name"],
        "is_playing": current["is_playing"],
        "progress_ms": current["progress_ms"],
        "duration_ms": item["duration_ms"],
        "device": current["device"]["name"] if current.get("device") else "?",
        "url": item["external_urls"]["spotify"],
    }


def play() -> None:
    get_client().start_playback()


def pause() -> None:
    get_client().pause_playback()


def next_track() -> None:
    get_client().next_track()


def previous_track() -> None:
    get_client().previous_track()


def set_volume(percent: int) -> None:
    percent = max(0, min(100, percent))
    get_client().volume(percent)


def list_devices() -> list:
    return get_client().devices()["devices"]


def set_active_device(device_id: str) -> None:
    get_client().transfer_playback(device_id, force_play=False)


def list_playlists(limit: int = 20) -> list:
    results = get_client().current_user_playlists(limit=limit)
    return [
        {"id": p["id"], "name": p["name"], "tracks": p["tracks"]["total"]}
        for p in results["items"]
    ]


def play_playlist(playlist_id: str) -> None:
    get_client().start_playback(context_uri=f"spotify:playlist:{playlist_id}")


def search_and_play(query: str):
    results = get_client().search(q=query, type="track", limit=1)
    items = results["tracks"]["items"]
    if not items:
        return None
    track = items[0]
    get_client().start_playback(uris=[track["uri"]])
    return f'{track["name"]} - {", ".join(a["name"] for a in track["artists"])}'
