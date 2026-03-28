"""
tray_app.py — System tray icon for Desktop Cat.
Runs in a background thread; dispatches to Tkinter via root.after().
"""

import threading
import pystray
from PIL import Image, ImageDraw
import sprites
import startup


def _make_icon_image(size=64) -> Image.Image:
    orange = (244, 162, 52)
    dark   = (180, 100, 20)
    green  = (90,  190, 70)
    black  = (25,   25, 25)
    pink   = (255, 155,175)

    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    s    = size

    draw.polygon([(s*6//16,s*4//16),(s*9//16,s*1//16),(s*12//16,s*4//16)], fill=orange)
    draw.polygon([(s*4//16,s*4//16),(s*7//16,s*1//16),(s*10//16,s*4//16)], fill=orange)
    draw.ellipse([s*2//16,s*3//16,s*14//16,s*14//16], fill=orange, outline=dark, width=1)
    draw.polygon([(s*7//16,s*4//16),(s*9//16,s*2//16),(s*11//16,s*4//16)], fill=pink)
    draw.polygon([(s*5//16,s*4//16),(s*7//16,s*2//16),(s*9//16, s*4//16)], fill=pink)
    draw.ellipse([s*4//16,s*5//16,s*7//16,s*8//16],  fill=green)
    draw.ellipse([s*9//16,s*5//16,s*12//16,s*8//16], fill=green)
    draw.ellipse([s*5//16,s*6//16,s*6//16,s*7//16],  fill=black)
    draw.ellipse([s*10//16,s*6//16,s*11//16,s*7//16],fill=black)
    draw.polygon([(s*7//16,s*9//16),(s*9//16,s*9//16),(s*8//16,s*11//16)], fill=pink)
    draw.arc([s*6//16,s*10//16,s*8//16,s*12//16],  0, 180, fill=black, width=1)
    draw.arc([s*8//16,s*10//16,s*10//16,s*12//16], 0, 180, fill=black, width=1)
    return img


class TrayApp:
    def __init__(self, pet):
        self._pet  = pet
        self.icon  = None

    def run(self):
        icon_img = _make_icon_image(64)

        def _dispatch(fn):
            self._pet.root.after(0, fn)

        # ── Costume items ──────────────────────────────────────────────────
        costume_items = [
            pystray.MenuItem(
                name.title(),
                lambda _, __, c=name: _dispatch(lambda: self._pet.set_costume(c)),
            )
            for name in sprites.COSTUMES
        ]

        # ── Corner items ──────────────────────────────────────────────────
        corner_labels = {
            "bottom-right": "↘  Bottom-right",
            "bottom-left":  "↙  Bottom-left",
            "top-right":    "↗  Top-right",
            "top-left":     "↖  Top-left",
        }
        corner_items = [
            pystray.MenuItem(
                label,
                lambda _, __, c=corner: _dispatch(lambda: self._pet.set_corner(c)),
            )
            for corner, label in corner_labels.items()
        ]

        # ── Actions ───────────────────────────────────────────────────────
        def say_something(icon, item):
            from phrases import get_phrase
            phrase = get_phrase(self._pet._app_context)
            _dispatch(lambda: (
                self._pet.show_bubble(phrase),
                self._pet._set_state("happy", lock_ms=3_500),
            ))

        def feed_cat(icon, item):
            _dispatch(self._pet.feed)

        def wander(icon, item):
            _dispatch(self._pet.wander)

        def show_pet(icon, item):
            _dispatch(self._pet.show)

        def toggle_startup(icon, item):
            if startup.is_enabled():
                startup.disable()
            else:
                startup.enable()

        def exit_app(icon, item):
            icon.stop()
            self._pet.root.after(0, self._pet.quit)

        # ── Menu ──────────────────────────────────────────────────────────
        menu = pystray.Menu(
            pystray.MenuItem("🐱  Desktop Cat", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Show cat",            show_pet),
            pystray.MenuItem("💬  Say something!",  say_something),
            pystray.MenuItem("🐟  Feed the cat",    feed_cat),
            pystray.MenuItem("🚶  Go for a walk",   wander),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("🎨  Costume",  pystray.Menu(*costume_items)),
            pystray.MenuItem("📌  Position", pystray.Menu(*corner_items)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Start on boot",
                toggle_startup,
                checked=lambda _: startup.is_enabled(),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", exit_app),
        )

        self.icon = pystray.Icon("DesktopCat", icon_img, "Desktop Cat 🐱", menu)
        self.icon.run()
