"""
seasonal.py — Returns seasonal costume suggestions and extra phrases.

Called once at startup and whenever the user opens settings.
"""

from datetime import date


def get_season_info() -> dict:
    """
    Returns a dict:
        suggested_costume : str | None   (None = use saved preference)
        phrases           : list[str]    (extra seasonal phrases to add)
        greeting          : str | None   (first-launch greeting for the season)
    """
    today = date.today()
    m, d  = today.month, today.day

    # ── Halloween: Oct 20 – Nov 2
    if (m == 10 and d >= 20) or (m == 11 and d <= 2):
        return {
            "suggested_costume": "spooky",
            "phrases": [
                "Meoooow... 👻 (that was a ghost impression)",
                "Happy Halloween! 🎃 Don't eat ALL the candy.",
                "Spooky season! I turned into a black cat. Fitting.",
                "Boo! Did I scare you? Good. 🦇",
            ],
            "greeting": "Happy Halloween! 🎃 I dressed up for the occasion.",
        }

    # ── Christmas: Dec 15 – Dec 31
    if m == 12 and d >= 15:
        return {
            "suggested_costume": "christmas",
            "phrases": [
                "Ho ho ho! 🎅 Keep up the good work!",
                "You're on the nice list, I checked. ✨",
                "Almost time for a well-earned rest! 🎄",
                "Meowy Christmas! 🐱🎁",
            ],
            "greeting": "Meowy Christmas! 🎄 I put on something festive.",
        }

    # ── New Year: Jan 1 – Jan 5
    if m == 1 and d <= 5:
        return {
            "suggested_costume": None,
            "phrases": [
                "Happy New Year! 🎆 Big things ahead for you!",
                "New year, still your biggest fan. 🎉",
                "Whatever your resolution is — you've got this!",
            ],
            "greeting": "Happy New Year! 🎆 Let's make it a great one.",
        }

    # ── Valentine's Day: Feb 10 – Feb 14
    if m == 2 and 10 <= d <= 14:
        return {
            "suggested_costume": "valentine",
            "phrases": [
                "Happy Valentine's Day! 💕 You are loved.",
                "You deserve all the good things today. 🌹",
                "Being your desktop companion is my favourite job. ❤️",
            ],
            "greeting": "Happy Valentine's Day! 💕 I dressed in pink for you.",
        }

    # ── Summer (Northern Hemisphere): Jun 21 – Sep 22
    if (m == 6 and d >= 21) or m in (7, 8) or (m == 9 and d <= 22):
        return {
            "suggested_costume": None,
            "phrases": [
                "Stay hydrated! ☀️ It's hot out there.",
                "Summer mode: activated. Don't forget sunscreen! 🌞",
                "You're radiating great energy today. Like the sun.",
            ],
            "greeting": None,
        }

    # ── Default: no seasonal override
    return {
        "suggested_costume": None,
        "phrases": [],
        "greeting": None,
    }
