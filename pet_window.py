"""
pet_window.py — The interactive desktop cat window.

State machine
─────────────
  idle       default; blinks randomly
  happy      triggered by click / encouragement / wakeup
  walk       wandering to a new screen position
  sleep      user has been idle >5 min OR energy very low
  stressed   CPU usage is very high
  eat        user fed the cat from tray
  dance      music app detected

Priority (highest wins):
  stressed > eat > dance > sleep > happy > walk > idle

External triggers arrive via root.after() from watcher threads.
"""

import random
import tkinter as tk
from datetime import datetime
from PIL import ImageTk

import config
import sprites
from mood    import MoodState
from phrases import get_phrase
from seasonal import get_season_info

CHROMA = "#FF00FF"

# How many pixels to move per step when walking across the screen
WALK_STEP = 6
WALK_STEP_MS = 30   # ms between steps (lower = faster)

# Mood HUD font / colors
HUD_BG     = "#1E1E2E"
HUD_FG     = "#CDD6F4"
HUD_BORDER = "#585B70"


# ──────────────────────────────────────────────────────────────────────────────
#  Speech bubble
# ──────────────────────────────────────────────────────────────────────────────

class Bubble(tk.Toplevel):
    BG     = "#FFFDE7"
    FG     = "#333333"
    BORDER = "#D4C040"
    FONT   = ("Segoe UI", 10)

    def __init__(self, parent, text):
        super().__init__(parent)
        self.overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.configure(bg=self.BORDER)

        inner = tk.Frame(self, bg=self.BG, padx=12, pady=8)
        inner.pack(padx=2, pady=2)

        tk.Label(
            inner, text=text, bg=self.BG, fg=self.FG,
            font=self.FONT, wraplength=230, justify="left",
        ).pack()


# ──────────────────────────────────────────────────────────────────────────────
#  Mood HUD
# ──────────────────────────────────────────────────────────────────────────────

class MoodHUD(tk.Toplevel):
    FONT_MONO = ("Consolas", 9)

    def __init__(self, parent):
        super().__init__(parent)
        self.overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.configure(bg=HUD_BORDER)

        inner = tk.Frame(self, bg=HUD_BG, padx=10, pady=8)
        inner.pack(padx=1, pady=1)

        tk.Label(
            inner, text="  CAT STATUS  ", bg=HUD_BG, fg="#89B4FA",
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w")

        self._var = tk.StringVar()
        tk.Label(
            inner, textvariable=self._var,
            bg=HUD_BG, fg=HUD_FG,
            font=self.FONT_MONO,
            justify="left",
        ).pack(anchor="w", pady=(4, 0))

    def update_text(self, text: str):
        self._var.set(text)


# ──────────────────────────────────────────────────────────────────────────────
#  Pet window
# ──────────────────────────────────────────────────────────────────────────────

class PetWindow:
    BUBBLE_DURATION = 5_500
    BLINK_MS        = 130
    MOOD_TICK_MS    = 60_000   # tick mood every minute

    def __init__(self, root: tk.Tk):
        self.root = root
        self.cfg  = config.load()

        self._costume = self.cfg["costume"]
        self._corner  = self.cfg["corner"]
        self._scale   = self.cfg.get("scale", 4)

        # State
        self._state     = "idle"
        self._frame_idx = 0
        self._locked    = False      # True while a high-priority state plays

        # Context from AppWatcher
        self._app_context = "other"

        # Walk target
        self._walk_tx = 0
        self._walk_ty = 0

        # After() handles
        self._anim_job     = None
        self._bubble_job   = None
        self._enc_job      = None
        self._walk_job     = None
        self._hud_job      = None

        # Widgets
        self._bubble_win: Bubble | None  = None
        self._hud_win:    MoodHUD | None = None

        # Drag
        self._drag_ox  = 0
        self._drag_oy  = 0
        self._dragging = False

        # Mood
        self.mood = MoodState()

        # Sprites
        self._tk_frames: dict[str, list] = {}

        # Setup
        self._setup_window()
        self._reload_sprites()
        self._setup_canvas()
        self._position()
        self._bind()
        self._animate()
        self._schedule_encouragement()
        self._schedule_mood_tick()

        # Seasonal greeting
        info = get_season_info()
        from phrases import add_seasonal_phrases
        if info["phrases"]:
            add_seasonal_phrases(info["phrases"])
        if info["suggested_costume"] and self.cfg.get("costume") == "orange":
            # Only auto-apply seasonal costume if user hasn't changed it
            self.root.after(2000, lambda: self.set_costume(info["suggested_costume"]))
        if info["greeting"]:
            self.root.after(1500, lambda: self.show_bubble(info["greeting"]))

        # Greet by time of day on startup
        self.root.after(500, self._time_of_day_greeting)

    # ── Window ────────────────────────────────────────────────────────────────

    def _setup_window(self):
        self.root.title("Desktop Cat")
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", CHROMA)
        self.root.configure(bg=CHROMA)
        self.root.resizable(False, False)

    def _reload_sprites(self):
        self._tk_frames = {}
        for anim in sprites.ANIMATIONS:
            pil_list = sprites.get_frames(anim, self._costume, self._scale)
            self._tk_frames[anim] = [ImageTk.PhotoImage(img) for img in pil_list]
        sample = self._tk_frames["idle"][0]
        self._sprite_w = sample.width()
        self._sprite_h = sample.height()

    def _setup_canvas(self):
        pad = 4
        self._pad = pad
        cw = self._sprite_w + pad * 2
        ch = self._sprite_h + pad * 2
        self._canvas = tk.Canvas(
            self.root, width=cw, height=ch,
            bg=CHROMA, highlightthickness=0, bd=0,
        )
        self._canvas.pack()
        self._sprite_id = self._canvas.create_image(
            pad, pad, anchor="nw", image=self._tk_frames["idle"][0],
        )
        self._cw, self._ch = cw, ch

    # ── Positioning ───────────────────────────────────────────────────────────

    def _corner_coords(self, corner=None):
        corner = corner or self._corner
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        m  = 12
        tb = 48
        return {
            "bottom-right": (sw - self._cw - m,  sh - self._ch - m - tb),
            "bottom-left":  (m,                   sh - self._ch - m - tb),
            "top-right":    (sw - self._cw - m,   m),
            "top-left":     (m,                   m),
        }[corner]

    def _position(self, corner=None):
        x, y = self._corner_coords(corner)
        self.root.geometry(f"+{x}+{y}")

    def _current_xy(self):
        return self.root.winfo_x(), self.root.winfo_y()

    # ── Bindings ──────────────────────────────────────────────────────────────

    def _bind(self):
        self._canvas.bind("<Button-1>",         self._on_press)
        self._canvas.bind("<B1-Motion>",        self._on_move)
        self._canvas.bind("<ButtonRelease-1>",  self._on_release)
        self._canvas.bind("<Double-Button-1>",  self._on_double_click)
        self._canvas.bind("<Button-3>",         self._on_rclick)
        self._canvas.bind("<Enter>",            self._on_hover)
        self._canvas.bind("<Leave>",            self._on_leave)

    def _on_press(self, e):
        self._drag_ox  = e.x_root - self.root.winfo_x()
        self._drag_oy  = e.y_root - self.root.winfo_y()
        self._dragging = False

    def _on_move(self, e):
        self._dragging = True
        self._cancel_walk()
        nx = e.x_root - self._drag_ox
        ny = e.y_root - self._drag_oy
        self.root.geometry(f"+{nx}+{ny}")

    def _on_release(self, e):
        if not self._dragging:
            self._single_click()

    def _on_double_click(self, e):
        self._dragging = False
        self._double_click()

    def _on_hover(self, e):
        self._show_hud()

    def _on_leave(self, e):
        self._hide_hud()

    def _single_click(self):
        """Single click: give encouragement, go happy, pet the mood."""
        self.mood.pet()
        phrase = get_phrase(self._app_context)
        self.show_bubble(phrase)
        self._set_state("happy", lock_ms=3_500)

    def _double_click(self):
        """Double click: cycle through a fun animation."""
        options = ["eat", "dance", "happy"]
        state   = random.choice(options)
        if state == "eat":
            self.mood.feed()
            self.show_bubble("Nom nom nom! 🐟 Yummy!")
        elif state == "dance":
            self.show_bubble("🎵 *zooms around the screen*")
        self._set_state(state, lock_ms=4_000)

    def _on_rclick(self, e):
        m = tk.Menu(self.root, tearoff=0)
        m.add_command(label="💬  Say something!", command=self._single_click)
        m.add_command(label="🐟  Feed the cat",   command=self._feed)
        m.add_separator()

        # Mood display
        summary = self.mood.summary()
        for line in summary.split("\n"):
            m.add_command(label=f"  {line}", state="disabled")
        m.add_separator()

        # Costume
        cm = tk.Menu(m, tearoff=0)
        for c in sprites.COSTUMES:
            cm.add_command(label=c.title(), command=lambda c=c: self.set_costume(c))
        m.add_cascade(label="🎨  Costume", menu=cm)

        # Corner
        pm = tk.Menu(m, tearoff=0)
        for corner in ("bottom-right", "bottom-left", "top-right", "top-left"):
            pm.add_command(
                label=corner.replace("-", " ").title(),
                command=lambda c=corner: self.set_corner(c),
            )
        m.add_cascade(label="📌  Position", menu=pm)
        m.add_separator()
        m.add_command(label="✖  Hide", command=self.root.withdraw)
        m.tk_popup(e.x_root, e.y_root)

    # ── State machine ─────────────────────────────────────────────────────────

    def _set_state(self, state: str, lock_ms: int = 0):
        if self._locked and state not in ("stressed",):
            return
        self._state     = state
        self._frame_idx = 0
        if lock_ms:
            self._locked = True
            self.root.after(lock_ms, self._unlock)

    def _unlock(self):
        self._locked = False
        self._set_state("idle")

    # ── Animation loop ────────────────────────────────────────────────────────

    def _animate(self):
        frames = self._tk_frames.get(self._state, self._tk_frames["idle"])

        if self._state == "idle":
            # Eyes open most of the time; brief blink via IDLE_BLINK
            self._canvas.itemconfig(self._sprite_id, image=frames[0])
            delay = random.randint(3_200, 6_800)
            # Schedule blink inside the delay
            blink_at = random.randint(500, max(500, delay - 300))
            self.root.after(blink_at, self._do_blink)
        else:
            img = frames[self._frame_idx % len(frames)]
            self._canvas.itemconfig(self._sprite_id, image=img)
            self._frame_idx += 1
            delay = {
                "walk":     220,
                "dance":    240,
                "eat":      300,
                "sleep":    900,
                "stressed": 180,
                "happy":    260,
            }.get(self._state, 260)

        self._anim_job = self.root.after(delay, self._animate)

    def _do_blink(self):
        frames = self._tk_frames.get("idle", [])
        if len(frames) > 1 and self._state == "idle":
            self._canvas.itemconfig(self._sprite_id, image=frames[1])
            self.root.after(self.BLINK_MS, self._end_blink)

    def _end_blink(self):
        frames = self._tk_frames.get("idle", [])
        if frames and self._state == "idle":
            self._canvas.itemconfig(self._sprite_id, image=frames[0])

    # ── Walking across the screen ─────────────────────────────────────────────

    def wander(self):
        """Pick a random on-screen spot and walk there."""
        if self._locked:
            return
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        margin = 20
        tb     = 48
        self._walk_tx = random.randint(margin, sw - self._cw - margin)
        self._walk_ty = random.randint(margin, sh - self._ch - margin - tb)
        self._set_state("walk")
        self._walk_step()

    def _walk_step(self):
        cx, cy = self._current_xy()
        dx = self._walk_tx - cx
        dy = self._walk_ty - cy
        dist = (dx**2 + dy**2) ** 0.5

        if dist < WALK_STEP:
            # Arrived
            self.root.geometry(f"+{self._walk_tx}+{self._walk_ty}")
            self._set_state("idle")
            return

        nx = cx + int(dx / dist * WALK_STEP)
        ny = cy + int(dy / dist * WALK_STEP)
        self.root.geometry(f"+{nx}+{ny}")
        self._walk_job = self.root.after(WALK_STEP_MS, self._walk_step)

    def _cancel_walk(self):
        if self._walk_job:
            self.root.after_cancel(self._walk_job)
            self._walk_job = None
        if self._state == "walk":
            self._set_state("idle")

    # ── Encouragement scheduler ───────────────────────────────────────────────

    def _schedule_encouragement(self):
        base  = self.cfg.get("phrase_interval_minutes", 15) * 60_000
        delay = int(base * random.uniform(0.7, 1.3))
        self._enc_job = self.root.after(delay, self._random_encourage)

    def _random_encourage(self):
        context = self._app_context
        if self.mood.is_hungry:
            context = "hungry"
        elif self.mood.is_lonely:
            context = "lonely"
        self.show_bubble(get_phrase(context))
        self._set_state("happy", lock_ms=3_500)
        self._schedule_encouragement()
        # Occasionally wander after encouraging
        if random.random() < 0.3:
            self.root.after(4_500, self.wander)

    # ── Mood tick ─────────────────────────────────────────────────────────────

    def _schedule_mood_tick(self):
        self._mood_job = self.root.after(self.MOOD_TICK_MS, self._do_mood_tick)

    def _do_mood_tick(self):
        self.mood.tick()
        self._schedule_mood_tick()

    # ── Time-of-day greeting ──────────────────────────────────────────────────

    def _time_of_day_greeting(self):
        hour = datetime.now().hour
        if 5 <= hour < 12:
            self.show_bubble(get_phrase("morning"))
        elif 22 <= hour or hour < 2:
            self.show_bubble(get_phrase("night"))

    # ── Watcher callbacks (called from watcher threads via root.after) ────────

    def on_user_idle(self):
        if not self._locked:
            self.mood.set_sleeping(True)
            self._set_state("sleep")
            self.show_bubble(get_phrase("sleepy"))

    def on_user_return(self):
        self.mood.set_sleeping(False)
        if self._state == "sleep":
            self._set_state("happy", lock_ms=3_000)
            self.show_bubble(get_phrase("wakeup"))

    def on_app_change(self, context: str):
        self._app_context = context
        if context == "music" and self._state not in ("sleep", "stressed"):
            self._set_state("dance", lock_ms=0)   # dance until music stops
            self.show_bubble(get_phrase("music"))
        elif context != "music" and self._state == "dance":
            self._set_state("idle")

    def on_system_stressed(self):
        self._set_state("stressed")
        self.show_bubble(get_phrase("stressed"))

    def on_system_calm(self):
        if self._state == "stressed":
            self._set_state("happy", lock_ms=2_500)
            self.show_bubble("Phew! That's better. 😮‍💨")

    def on_music_start(self):
        if self._state not in ("sleep", "stressed"):
            self._set_state("dance", lock_ms=0)
            self.show_bubble(get_phrase("music"))

    def on_music_stop(self):
        if self._state == "dance":
            self._set_state("idle")
            self.show_bubble("Aww, the music stopped... 🎵")

    # ── Feeding ───────────────────────────────────────────────────────────────

    def _feed(self):
        self.mood.feed()
        self._set_state("eat", lock_ms=3_000)
        self.show_bubble("Nom nom nom! 🐟 Thank you!")

    # ── Bubble ────────────────────────────────────────────────────────────────

    def show_bubble(self, text: str):
        self._hide_bubble()
        self._bubble_win = Bubble(self.root, text)
        self._place_bubble()
        self._bubble_job = self.root.after(self.BUBBLE_DURATION, self._hide_bubble)

    def _place_bubble(self):
        if not (self._bubble_win and self._bubble_win.winfo_exists()):
            return
        self._bubble_win.update_idletasks()
        bw = self._bubble_win.winfo_width()
        bh = self._bubble_win.winfo_height()
        cx = self.root.winfo_x()
        cy = self.root.winfo_y()
        x  = cx + self._cw // 2 - bw // 2
        y  = cy - bh - 6
        sw = self.root.winfo_screenwidth()
        x  = max(4, min(x, sw - bw - 4))
        y  = max(4, y)
        self._bubble_win.geometry(f"+{x}+{y}")

    def _hide_bubble(self):
        if self._bubble_job:
            self.root.after_cancel(self._bubble_job)
            self._bubble_job = None
        if self._bubble_win and self._bubble_win.winfo_exists():
            self._bubble_win.destroy()
        self._bubble_win = None

    # ── Mood HUD ──────────────────────────────────────────────────────────────

    def _show_hud(self):
        if self._hud_win and self._hud_win.winfo_exists():
            return
        self._hud_win = MoodHUD(self.root)
        self._update_hud()

    def _hide_hud(self):
        if self._hud_win and self._hud_win.winfo_exists():
            self._hud_win.destroy()
        self._hud_win = None
        if self._hud_job:
            self.root.after_cancel(self._hud_job)
            self._hud_job = None

    def _update_hud(self):
        if not (self._hud_win and self._hud_win.winfo_exists()):
            return
        self._hud_win.update_text(self.mood.summary())
        # Position to the left of the cat
        self._hud_win.update_idletasks()
        hw = self._hud_win.winfo_width()
        hh = self._hud_win.winfo_height()
        cx = self.root.winfo_x()
        cy = self.root.winfo_y()
        x  = cx - hw - 8
        y  = cy + self._ch // 2 - hh // 2
        x  = max(4, x)
        self._hud_win.geometry(f"+{x}+{y}")
        self._hud_job = self.root.after(2000, self._update_hud)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_costume(self, costume: str):
        self._costume         = costume
        self.cfg["costume"]   = costume
        config.save(self.cfg)
        if self._anim_job:
            self.root.after_cancel(self._anim_job)
            self._anim_job = None
        self._reload_sprites()
        self._frame_idx = 0
        self._animate()

    def set_corner(self, corner: str):
        self._corner        = corner
        self.cfg["corner"]  = corner
        config.save(self.cfg)
        self._cancel_walk()
        self._position(corner)

    def feed(self):
        self._feed()

    def show(self):
        self.root.deiconify()
        self.root.lift()

    def quit(self):
        self.root.quit()
