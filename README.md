# 🐱 Desktop Cat

A tiny pixel-art cat that lives in the corner of your Windows desktop,
encourages you while you work, and never asks for food.

---

## Quick start

### 1 — Prerequisites
- Python 3.11 or later  
  Download: https://www.python.org/downloads/  
  ✅ Tick **"Add Python to PATH"** during install.

### 2 — Install dependencies
Open a terminal in this folder and run:

```
pip install -r requirements.txt
```

Or just double-click **`install_and_run.bat`** — it installs everything and
launches the cat in one step.

### 3 — Launch
```
pythonw main.py
```
(`pythonw` hides the console window. Use `python main.py` if you want to see
debug output.)

---

## Features

| Feature | How to access |
|---|---|
| **Encouragement bubbles** | Appear automatically every ~15 min |
| **Click the cat** | Instant bubble + happy face |
| **Drag the cat** | Click-and-drag to anywhere |
| **Right-click the cat** | Quick menu: say something, change costume/position |
| **System tray icon** | Full menu: costumes, corners, start-on-boot toggle |
| **5 costumes** | Orange, Black, White, Gray, Tuxedo |
| **4 positions** | Any corner of the screen |
| **Start on boot** | Toggle via tray menu (no admin rights needed) |

---

## Costumes

| Name | Description |
|---|---|
| **Orange** | Classic ginger tabby |
| **Black** | Sleek black cat with yellow eyes |
| **White** | Snow-white cat with blue eyes |
| **Gray** | Soft gray tabby |
| **Tuxedo** | Black cat, white belly — fancy! |

---

## Adding your own phrases

Open `phrases.py` and add strings to the `PHRASES` list. Emoji work fine!

---

## Configuration file

Settings are saved automatically to:

```
%APPDATA%\DesktopCat\config.json
```

You can edit this file directly if needed.

---

## Package as a standalone .exe (optional)

```
pip install pyinstaller
pyinstaller --noconsole --onefile --name DesktopCat main.py
```

The `.exe` will be in the `dist/` folder.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Cat window flickers | Make sure no other overlay software is interfering |
| Tray icon missing | Wait a couple of seconds; pystray may be slow to register |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |
| Cat invisible | Try changing Position via tray; taskbar height may differ |

---

## Project structure

```
virtual_cat/
├── main.py          Entry point
├── pet_window.py    Transparent Tkinter window + animation
├── sprites.py       Pixel art frames + renderer
├── tray_app.py      System tray icon (pystray)
├── config.py        Load / save settings (AppData)
├── startup.py       Windows login startup (registry)
├── phrases.py       Encouragement strings — edit freely!
├── requirements.txt Dependencies
└── install_and_run.bat  One-click setup for Windows
```

---

Made with 🐾 and Python.
