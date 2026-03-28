"""
mood.py — Tracks the cat's happiness, hunger and energy.

Values are all 0–100. They tick slowly over time and are saved to config.
"""

import time
import config

# How much each stat changes per real-world minute
HAPPINESS_DECAY  =  0.5   # slowly gets lonely if ignored
HUNGER_GROWTH    =  1.5   # gets hungry over time
ENERGY_DECAY     =  0.8   # tires out while awake
ENERGY_RECOVERY  =  3.0   # recovers quickly while sleeping

# Interaction bonuses
PET_HAPPINESS    = 12
FEED_HUNGER_DROP = 35
SLEEP_THRESHOLD  = 25     # energy below this → cat wants to sleep


class MoodState:
    def __init__(self):
        cfg = config.load()
        mood = cfg.get("mood", {})
        self.happiness: float = mood.get("happiness", 80.0)
        self.hunger:    float = mood.get("hunger",    20.0)
        self.energy:    float = mood.get("energy",    90.0)
        self._last_tick: float = time.monotonic()
        self._sleeping  = False

    # ── Tick ──────────────────────────────────────────────────────────────────

    def tick(self) -> None:
        """Call this periodically; it advances stats based on elapsed time."""
        now     = time.monotonic()
        minutes = (now - self._last_tick) / 60.0
        self._last_tick = now

        self.hunger    = min(100, self.hunger    + HUNGER_GROWTH   * minutes)
        self.happiness = max(  0, self.happiness - HAPPINESS_DECAY * minutes)

        if self._sleeping:
            self.energy = min(100, self.energy + ENERGY_RECOVERY * minutes)
        else:
            self.energy = max(  0, self.energy  - ENERGY_DECAY    * minutes)

        self._save()

    # ── Events ────────────────────────────────────────────────────────────────

    def pet(self) -> None:
        self.happiness = min(100, self.happiness + PET_HAPPINESS)
        self._save()

    def feed(self) -> None:
        self.hunger    = max(  0, self.hunger - FEED_HUNGER_DROP)
        self.happiness = min(100, self.happiness + 5)
        self._save()

    def set_sleeping(self, sleeping: bool) -> None:
        self._sleeping = sleeping

    # ── Queries ───────────────────────────────────────────────────────────────

    @property
    def wants_sleep(self) -> bool:
        return self.energy < SLEEP_THRESHOLD

    @property
    def is_hungry(self) -> bool:
        return self.hunger > 70

    @property
    def is_lonely(self) -> bool:
        return self.happiness < 30

    def summary(self) -> str:
        def bar(v):
            filled = round(v / 10)
            return "█" * filled + "░" * (10 - filled)

        h_label = "😸" if self.happiness > 60 else ("😐" if self.happiness > 30 else "😿")
        f_label = "🍣" if self.hunger < 40 else ("😋" if self.hunger < 70 else "🍽️")
        e_label = "⚡" if self.energy > 50 else ("😴" if self.energy < 25 else "🔋")

        return (
            f"{h_label} Mood:    {bar(self.happiness)}\n"
            f"{f_label} Hunger:  {bar(self.hunger)}\n"
            f"{e_label} Energy:  {bar(self.energy)}"
        )

    # ── Internal ──────────────────────────────────────────────────────────────

    def _save(self) -> None:
        cfg = config.load()
        cfg["mood"] = {
            "happiness": round(self.happiness, 1),
            "hunger":    round(self.hunger,    1),
            "energy":    round(self.energy,    1),
        }
        config.save(cfg)
