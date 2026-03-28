"""
watchers.py — Background monitors that fire callbacks to the Tkinter thread.

All callbacks must be called via root.after(0, fn) to stay thread-safe.
Each watcher runs in its own daemon thread and polls on a timer.

Watchers
--------
IdleWatcher      — detects when the user goes idle / returns (ctypes)
AppWatcher       — detects which window is in focus (ctypes)
SystemWatcher    — monitors CPU / RAM stress (psutil)
MusicWatcher     — detects if a music app is playing (window title scan)
"""

import ctypes
import threading
import time

try:
    import psutil
    _PSUTIL_OK = True
except ImportError:
    _PSUTIL_OK = False


# ── Helpers ───────────────────────────────────────────────────────────────────

class _LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]


def _get_idle_seconds() -> float:
    lii = _LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(_LASTINPUTINFO)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
    millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
    return millis / 1000.0


def _get_foreground_title() -> str:
    try:
        hwnd   = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf    = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value.lower()
    except Exception:
        return ""


def _all_window_titles() -> list[str]:
    """Return lowercase titles of all visible top-level windows."""
    titles = []

    def _enum_cb(hwnd, _):
        if ctypes.windll.user32.IsWindowVisible(hwnd):
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            if length:
                buf = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
                titles.append(buf.value.lower())
        return True

    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
    ctypes.windll.user32.EnumWindows(EnumWindowsProc(_enum_cb), 0)
    return titles


# ── App context classifier ────────────────────────────────────────────────────

APP_RULES = [
    # (keywords_in_title, context_name)
    (["visual studio", "vscode", "vs code", "pycharm", "intellij",
      "sublime text", "notepad++", "vim", "neovim", "emacs",
      ".py", ".js", ".ts", ".cpp", ".java", ".rs", "terminal",
      "powershell", "cmd.exe", "bash"],            "coding"),
    (["chrome", "firefox", "edge", "brave", "safari",
      "opera", "vivaldi"],                          "browsing"),
    (["youtube", "twitch", "netflix", "prime video",
      "disney+", "hulu", "plex"],                   "watching"),
    (["word", "docs", "pages", "libreoffice writer",
      ".docx", ".txt", "notepad", "notion"],         "writing"),
    (["excel", "sheets", "numbers", "libreoffice calc",
      ".xlsx", ".csv"],                              "spreadsheet"),
    (["figma", "photoshop", "illustrator", "gimp",
      "inkscape", "affinity", "canva"],              "designing"),
    (["slack", "teams", "discord", "zoom",
      "meet", "webex"],                              "meeting"),
    (["spotify", "itunes", "music", "winamp",
      "foobar", "vlc", "media player"],              "music"),
]

MUSIC_KEYWORDS = ["spotify", "itunes", "apple music", "winamp",
                  "foobar2000", "tidal", "deezer", "soundcloud"]


def classify_app(title: str) -> str:
    for keywords, context in APP_RULES:
        if any(kw in title for kw in keywords):
            return context
    return "other"


# ── Watcher base ──────────────────────────────────────────────────────────────

class _Watcher:
    def __init__(self, root, interval: float):
        self._root     = root
        self._interval = interval
        self._running  = False
        self._thread   = None

    def start(self):
        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            try:
                self._poll()
            except Exception:
                pass
            time.sleep(self._interval)

    def _poll(self):
        raise NotImplementedError

    def _dispatch(self, fn):
        """Thread-safe call into the Tkinter main loop."""
        if self._root and self._root.winfo_exists():
            self._root.after(0, fn)


# ── IdleWatcher ───────────────────────────────────────────────────────────────

class IdleWatcher(_Watcher):
    IDLE_THRESHOLD = 5 * 60   # seconds before "idle" fires

    def __init__(self, root, on_idle, on_active):
        super().__init__(root, interval=15)
        self._on_idle   = on_idle
        self._on_active = on_active
        self._was_idle  = False

    def _poll(self):
        idle = _get_idle_seconds() >= self.IDLE_THRESHOLD
        if idle and not self._was_idle:
            self._was_idle = True
            self._dispatch(self._on_idle)
        elif not idle and self._was_idle:
            self._was_idle = False
            self._dispatch(self._on_active)


# ── AppWatcher ────────────────────────────────────────────────────────────────

class AppWatcher(_Watcher):
    def __init__(self, root, on_app_change):
        super().__init__(root, interval=3)
        self._on_app_change = on_app_change
        self._last_context  = "other"

    def _poll(self):
        title   = _get_foreground_title()
        context = classify_app(title)
        if context != self._last_context:
            self._last_context = context
            ctx = context   # capture for lambda
            self._dispatch(lambda: self._on_app_change(ctx))


# ── SystemWatcher ─────────────────────────────────────────────────────────────

class SystemWatcher(_Watcher):
    CPU_STRESS_THRESHOLD = 80    # percent
    CPU_CALM_THRESHOLD   = 50

    def __init__(self, root, on_stressed, on_calm):
        super().__init__(root, interval=10)
        self._on_stressed  = on_stressed
        self._on_calm      = on_calm
        self._was_stressed = False

    def _poll(self):
        if not _PSUTIL_OK:
            return
        cpu = psutil.cpu_percent(interval=1)
        if cpu >= self.CPU_STRESS_THRESHOLD and not self._was_stressed:
            self._was_stressed = True
            self._dispatch(self._on_stressed)
        elif cpu < self.CPU_CALM_THRESHOLD and self._was_stressed:
            self._was_stressed = False
            self._dispatch(self._on_calm)


# ── MusicWatcher ──────────────────────────────────────────────────────────────

class MusicWatcher(_Watcher):
    def __init__(self, root, on_music_start, on_music_stop):
        super().__init__(root, interval=8)
        self._on_music_start = on_music_start
        self._on_music_stop  = on_music_stop
        self._was_playing    = False

    def _poll(self):
        titles  = _all_window_titles()
        playing = any(
            kw in t
            for t in titles
            for kw in MUSIC_KEYWORDS
        )
        if playing and not self._was_playing:
            self._was_playing = True
            self._dispatch(self._on_music_start)
        elif not playing and self._was_playing:
            self._was_playing = False
            self._dispatch(self._on_music_stop)
