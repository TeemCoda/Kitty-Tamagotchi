"""
phrases.py — Context-aware encouragement messages.

get_phrase(context)  returns a string appropriate for the current situation.

Contexts: None, "coding", "browsing", "watching", "writing",
          "spreadsheet", "designing", "meeting", "music",
          "stressed", "hungry", "lonely", "sleepy", "morning",
          "night", "wakeup", "return"
"""

import random

# ── General ───────────────────────────────────────────────────────────────────

GENERAL = [
    "You're doing amazing! Keep it up! ✨",
    "Meow! (That means: I believe in you.)",
    "One step at a time — you're getting there!",
    "Don't forget to blink! And drink water! 💧",
    "You're so much stronger than you think.",
    "Take a deep breath. You've got this.",
    "You've made it through every hard day so far. 100% streak!",
    "Time to stretch! Wiggle those fingers! 🐾",
    "Your ideas are brilliant — keep going!",
    "You're doing better than you give yourself credit for.",
    "Remember to save your work! 💾",
    "Small progress is still progress!",
    "You're the reason I sit here all day. ❤️",
    "Whatever you're working on — you can do it!",
    "Purrr... (you're doing great, I promise)",
    "I'm proud of you. Just wanted to say that.",
    "You deserve a little break if you need one!",
    "Every expert was once a beginner. Keep going!",
    "You handled that beautifully.",
    "Today you're 100% that boss. 😼",
    "Don't forget to look away from the screen for a sec!",
    "You are CRUSHING it right now.",
    "Sending you virtual head-bumps for luck! 🐱",
    "You're doing a great job being a person today.",
    "Have you had a snack? Don't forget to eat! 🍕",
    "Purrr",
]

# ── Context-specific ──────────────────────────────────────────────────────────

CODING = [
    "Debugging is just detective work. You're a detective. 🔍",
    "One more function and then a break? Deal!",
    "Your code is going to make someone's life easier. Keep at it!",
    "Ship it! (But maybe write a test first.) 🚢",
    "Stack Overflow? Never heard of it. You've got this. 😼",
    "Every great program started as a blank file. Look at you go!",
    "I don't understand what you're writing, but it looks impressive.",
    "Remember to commit! You'll thank yourself later. 💾",
    "Comments in your code = love letters to future-you. 📝",
    "Rubber duck debugging? I'm available. I'm basically a duck.",
]

BROWSING = [
    "Just a little procrastination break? I won't tell. 😏",
    "Taking a mental break is productive, actually. Science said so.",
    "Found anything interesting out there?",
    "Curiosity is a superpower. Keep exploring! 🌐",
    "Hey, at least close that one tab you've had open for 6 months.",
]

WATCHING = [
    "Watching something good? No spoilers, please.",
    "Entertainment is self-care! Enjoy your show. 📺",
    "A little downtime is important. You deserve it!",
    "...Are you watching cat videos? I support this.",
]

WRITING = [
    "Your words matter. Keep writing! ✍️",
    "Even rough drafts are progress. Don't delete it, fix it!",
    "Every great writer started with a messy first draft.",
    "You have things to say worth saying. Keep going!",
    "Writer's block is just your brain buffering. It'll load.",
]

SPREADSHEET = [
    "Spreadsheets: taming chaos, one cell at a time. You've got this.",
    "VLOOKUP? More like V-LOOKGREAT! ...sorry.",
    "Making those numbers behave. Respect. 📊",
    "The spreadsheet will not defeat you. You will defeat it.",
]

DESIGNING = [
    "Your eye for design is incredible. Keep creating! 🎨",
    "Art takes courage. You have it.",
    "Every pixel you place is intentional. Beautiful!",
    "Making the world prettier, one design at a time. 🖌️",
]

MEETING = [
    "You're killing it in there! 💼",
    "Meetings: necessary chaos. You're handling it great.",
    "Remember to mute when you're not talking! (from experience)",
    "Almost done! You've got great contributions to share.",
]

MUSIC = [
    "Oh! I like this one. *bopping intensifies* 🎵",
    "Good music = good productivity. You clearly know this.",
    "Playlist on point. Focus mode: activated. 🎶",
    "I'm dancing over here. Invisibly. But dancing.",
    "Excellent music taste confirmed. Carry on!",
]

# ── Mood / state specific ─────────────────────────────────────────────────────

STRESSED = [
    "Hey. Take a breath. The computer will still be there in 60 seconds.",
    "Your PC is working hard. So are you. Both deserve a break soon.",
    "High activity = progress! But don't forget to breathe. 💨",
    "Spinning fans = something's happening. You've got this.",
    "It's okay to step away for a moment. The work will wait.",
]

HUNGRY = [
    "Psst... when did you last eat? 🍜",
    "A hungry human is a less focused human. Snack time!",
    "You can't pour from an empty bowl. (Asking for a friend.) 🐾",
    "Food break! I'll watch the screen. (I won't do anything useful.)",
    "Your brain runs on glucose. Just saying. 🍕",
]

LONELY = [
    "Hey. I'm right here if you need a moment. 🐱",
    "You've been working hard. Don't forget you're appreciated.",
    "Come back and click me sometime! I like it when you do.",
    "Sending you a digital head-bump. 💙",
]

SLEEPY_PHRASES = [
    "zzz...",
    "...zzzz...",
    "*soft purring*",
    "zz... (just a little nap)",
]

WAKEUP = [
    "Oh! You're back! I missed you. 🐱",
    "*stretches* Good morning! Ready to go?",
    "Welcome back! I kept the screen warm.",
    "Oh hello! Napping was productive. For me.",
    "You're back! Let's get it! 💪",
]

MORNING = [
    "Good morning! ☀️ Today is going to be a great one.",
    "Rise and shine! You've got this day in the bag.",
    "Morning energy loading... ☕ You've got this!",
    "New day, fresh start. Let's go! 🌅",
]

NIGHT = [
    "Still at it? You're dedicated. Don't forget to sleep! 🌙",
    "Late night session? Make sure you rest soon. 💤",
    "The night owl grind is real. I respect it. But... bed soon?",
    "Burning the midnight oil! Impressive. Rest when you can. 🕯️",
]


# ── Context router ────────────────────────────────────────────────────────────

_CONTEXT_MAP = {
    "coding":      CODING,
    "browsing":    BROWSING,
    "watching":    WATCHING,
    "writing":     WRITING,
    "spreadsheet": SPREADSHEET,
    "designing":   DESIGNING,
    "meeting":     MEETING,
    "music":       MUSIC,
    "stressed":    STRESSED,
    "hungry":      HUNGRY,
    "lonely":      LONELY,
    "sleepy":      SLEEPY_PHRASES,
    "wakeup":      WAKEUP,
    "morning":     MORNING,
    "night":       NIGHT,
}


def get_phrase(context: str | None = None) -> str:
    pool = _CONTEXT_MAP.get(context, [])
    if pool and random.random() < 0.75:
        return random.choice(pool)
    return random.choice(GENERAL)


def add_seasonal_phrases(phrases: list[str]) -> None:
    """Inject seasonal phrases into the general pool at runtime."""
    GENERAL.extend(phrases)
