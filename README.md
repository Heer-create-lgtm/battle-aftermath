# Battle Aftermath – Top-Down Action-RPG

## Overview

*Battle Aftermath* is a retro, action-packed survival game built in Python using the Pygame library. Set in a post-apocalyptic zombie-infested world, players
experience a gripping narrative through varied gameplay phases—from intense tutorials and dramatic boss battles to unique revival mechanics and divine interventions. 
The game combines fast-paced combat with an immersive story, challenging players to master a blend of melee, ranged, and strategic shield attacks in their fight
against the undead.

A narrative-driven, top-down shooter / action-RPG built with Python 3 and Pygame.  Fight grotesque zombies, corrupted gods and screen-filling bosses while uncovering the story of a betrayed hero.

---

## Quick Start

1. **Install dependencies**
   Make sure you have Python 3 installed. Then, install Pygame using pip:
   ```bash
   pip install pygame
   ```
2. **Run the game**
   ```bash
   python3 main.py
   ```

> Tested with **Python 3.9+** and **Pygame 2.6+** on macOS & Windows.

---

## Features

- **Dynamic Difficulty** – `Calm Fury` passive boosts speed & damage when health <30 %.
- **Shield Mechanics** – toggleable guard that drains energy or throw it boomerang-style.
- **Level-Exclusive Mechanics** – e.g., Level 4 spawns **medkits** when health <20 % and you slay enemies.
- **Boss Variety** – Python serpent (burrow & charge), corrupted War-God with multi-phase AI, mini-bosses.
- **Collectibles & Upgrades** – hidden artifacts in various levels.
- **Slick Visual FX** – blood splatters, shield trails, particle pickups.
- **Modular Codebase** – each level isolated in `levels/` for easy expansion.
- **Unique Revival** - A distinctive revival system where in-game scientists provide a lifeline, allowing players to continue their journey despite setbacks.

## Controls

| Action                    | Key / Mouse |
|---------------------------|-------------|
| Move                      | **W A S D** |
| Aim                       | **Mouse**   |
| Fire                      | **Space** |
| Shield / Guard            | **E** |
| Sprint                    | **Left Shift** |
| Reload                    | **R** |
| Ground-Pound (charge & release) | **F** (hold) |
| Shield Throw              | **Q** |

`Esc` currently returns to the main menu or exits certain modes (e.g. Endless).  A universal in-game pause is **not implemented yet**.

---

## Game Flow & Levels

1. **Tutorial** – learn movement, sprinting, shooting, shielding, ground-pound charging, and shield-throwing.
2. **Ruined Sanctuary** – confront a remorseful lesser god; choose power upgrade paths.
3. **Divine Arena** – boss rush hosted by the corrupted War-God Kratos.
4. **Python Boss Fight** – survive the burrowing serpent and its minions.
5. **Revival Lab & Outside Quest** – after defeat, wake in the scientist’s lab, collect zombie blood samples outside to fully revive.
6. **Endless Mode** – optional survival mode accessible from main menu.
7. **Multiple Endings** – depending on the level the player dies different endings are played

Hidden collectibles (`collection1-5.png`) are scattered across areas – shoot crates/pillars or explore to reveal them.

---
## Assets & Directory Layout

```
assets/
  sprites/        # PNG artwork for characters, bosses, collectibles, UI
  music/          # OGG soundtrack & SFX
levels/           # Scene scripts & per-level logic
ui.py               # HUD rendering helpers
mechanics.py      # Core player physics & interactions
main.py           # Game state machine & entry point
settings.py       # Global constants (tile size, colours, etc.)
```

---

## Abilities & Upgrades

| Ability | Default Key | Description |
|---------|-------------|-------------|
| Shield Throw | Q (tap) | Launches shield forward, rebounds off obstacles, and returns. No energy cost but has a cooldown. |
| Guard / Block | E (hold) | Raise shield to block frontal damage while draining shield energy. |
| Calm Fury | Passive | When HP <30 %, gain +35 % move speed & +50 % bullet damage. |

---