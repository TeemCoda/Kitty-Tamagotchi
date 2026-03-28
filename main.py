"""
main.py — Entry point for Desktop Cat.

Run with: pythonw main.py   (no console window)
       or: python main.py    (with console for debugging)
"""

import threading
import tkinter as tk


def main():
    root = tk.Tk()

    from pet_window import PetWindow
    from tray_app   import TrayApp
    from watchers   import IdleWatcher, AppWatcher, SystemWatcher, MusicWatcher

    pet  = PetWindow(root)
    tray = TrayApp(pet)

    # ── Background watchers ───────────────────────────────────────────────────
    watchers = [
        IdleWatcher(
            root,
            on_idle   = pet.on_user_idle,
            on_active = pet.on_user_return,
        ),
        AppWatcher(
            root,
            on_app_change = pet.on_app_change,
        ),
        SystemWatcher(
            root,
            on_stressed = pet.on_system_stressed,
            on_calm     = pet.on_system_calm,
        ),
        MusicWatcher(
            root,
            on_music_start = pet.on_music_start,
            on_music_stop  = pet.on_music_stop,
        ),
    ]

    for w in watchers:
        w.start()

    # pystray blocks its thread
    t = threading.Thread(target=tray.run, daemon=True)
    t.start()

    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        for w in watchers:
            w.stop()


if __name__ == "__main__":
    main()
