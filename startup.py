"""
startup.py — Add / remove the app from Windows login startup via the registry.
Uses HKCU so no admin rights required.
"""

import os
import sys

APP_NAME = "DesktopCat"
REG_KEY  = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _get_launch_cmd() -> str:
    """Return the command string to launch this script without a console window."""
    if getattr(sys, "frozen", False):
        # Running as a PyInstaller .exe
        return f'"{sys.executable}"'
    # Running as a plain .py — use pythonw to suppress the console window
    python  = sys.executable
    pythonw = python.replace("python.exe", "pythonw.exe")
    if not os.path.exists(pythonw):
        pythonw = python            # fall back if pythonw not found
    script = os.path.abspath(__file__).replace("startup.py", "main.py")
    return f'"{pythonw}" "{script}"'


def is_enabled() -> bool:
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY)
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def enable() -> None:
    import winreg
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_SET_VALUE
    )
    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _get_launch_cmd())
    winreg.CloseKey(key)


def disable() -> None:
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
    except Exception:
        pass
