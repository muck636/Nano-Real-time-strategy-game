# Nano RTS

> **Strongly recommended: turn on God Mode at the beginning of every match.** Game balance is still being improved, so God Mode is the recommended way to play and learn. After choosing a faction and entering the match, press **Enter**, type `god`, and press **Enter** again. The right panel will show `GOD MODE` and `Credits INF`.

## What is this game?

Nano RTS is a single-player real-time strategy game. In an RTS, both sides act at the same time: you build a base, produce tanks, move them around the map, and attack an opponent controlled by the computer.

Your goal is to **destroy every enemy building** before the enemy destroys yours. Destroying the enemy's starting base alone is not enough if other enemy buildings remain.

## Start the game

On Windows, open PowerShell in the project folder and run:

```powershell
.\.venv\Scripts\python.exe main.py
```

If the virtual environment does not exist, install Python 3.11 first, then run these commands in the project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install pygame==2.6.1
.\.venv\Scripts\python.exe main.py
```

## Your first match

1. On the title screen, choose **A** or **B**. A is the blue side on the left; B is the red side on the right. Either is fine for your first game.
2. As soon as the match starts, press **Enter**, type `god`, and press **Enter** again. Look for `GOD MODE` and `Credits INF` on the right.
3. You begin with a Construction Yard and a Power Plant, but no tanks. In the right-hand **BUILD** menu, click **War Factory**, then left-click empty ground near one of your completed buildings. A green preview means the location is valid; red means it is not.
4. Left-click the completed War Factory. Its tank buttons appear at the bottom right. Click the first tank portrait to produce a unit; in God Mode it appears immediately if there is room nearby.
5. Left-click your tank to select it, then right-click open ground to move it. To select several tanks, hold the left mouse button and drag a box around them.
6. Use **WASD**, the arrow keys, or the minimap to look toward the other side of the map. With your tank selected, right-click an enemy building or tank to attack it. Your units can also attack nearby enemies automatically.
7. Destroy every enemy building to win. The computer will build and attack as well, so defend your own buildings.

## Basic controls

| Action | How to do it |
| --- | --- |
| Move the camera | Use **WASD** or the arrow keys, move the mouse to the edge of the battlefield, or left-click the minimap. |
| Select one unit or building | Left-click your unit or building. A diamond marks the selection. |
| Select several tanks | Hold the left mouse button and drag a box around them. |
| Move selected tanks | Right-click open ground. Green lines show movement orders. |
| Attack an enemy | Right-click an enemy unit or building. Red lines show attack orders. |
| Place a building | Left-click its button under **BUILD**, then left-click a valid location on the map. |
| Cancel building placement | Right-click or press **Esc**. |
| Open the console | Press **Enter** during a match. The match pauses while the console is open. |
| Start over | Press **R** to return to faction selection. This immediately ends the current match. |

Close the game using the window's close button. On the result screen, **Esc** also quits. When you select an object, the right-hand **SELECTION** area shows its health as `HP current / maximum`.

## God Mode

God Mode gives **your side** unlimited credits and instant building construction and tank production. Buildings already under construction finish when you enable it. Queued tanks are released when there is room near their factory. The computer does not receive these benefits.

God Mode **does not make your units or buildings invincible**. You still need valid building locations, a completed War Factory to produce tanks, and a completed Tech Center for advanced tanks and advanced defenses. Power is still needed for systems such as mines and defensive towers.

To turn God Mode off, press **Enter**, type `god off`, and press **Enter** again. You can press **Esc** to close the console without running a command.

## Buildings, credits, and power

| Building | What it does |
| --- | --- |
| **Construction Yard** | Your starting base. You need a completed Construction Yard to place more buildings. It cannot be sold. |
| **Mine** | Place it on a gold deposit. Each powered mine automatically earns 30 credits per second; there are three deposits near each starting base. |
| **Power Plant** | Supplies power. Build more if your demand becomes greater than your supply. |
| **War Factory** | Produces tanks. Select a completed factory to see its tank buttons. |
| **Tech Center** | Unlocks each faction's second tank and advanced defensive tower. |
| **Defensive towers** | Automatically attack enemies in range. The advanced tower requires a completed Tech Center. |

At the top right, **Credits** shows your money and **Power** shows `supply / demand`. If demand exceeds supply, mines and defenses stop working, and normal construction and production can pause. God Mode's instant player construction and production still apply.

New buildings must be near an existing completed friendly building. They cannot overlap other buildings or be placed on water or mountains. Only mines can be placed on gold deposits.

Select a completed, damaged building and click **Repair** to repair it; click **Stop Repair** to stop. Repairs use credits unless God Mode is enabled. **Sell** removes a selected building and returns part of its cost, depending on its remaining health. The Construction Yard cannot be sold.

## Tank types

- **Faction A: Guardian** can fire while moving. **Mirage** has longer range but must stop and turn its whole body toward the target before firing.
- **Faction B: Hammer** can fire while moving. **Apocalypse** is tougher, but must stop and rotate its turret into position before firing.

The second tank for either faction requires a completed Tech Center. Sea and mountains block all tanks. The minimap's yellow rectangle shows the area currently visible on screen; clicking the minimap moves the camera, not your units.

## Common problems

- **`No module named pygame`:** in the project folder, run `.\.venv\Scripts\python.exe -m pip install pygame==2.6.1`.
- **Nothing happens when I press Enter:** choose a faction and enter a match first; the console is available during a match.
- **`Tech Center required`:** build and finish a Tech Center before producing a second-tier tank or building an advanced tower.
- **`Place on a gold deposit`:** select **Mine** and click one of the gold deposits near your base.
- **`Outside build range` or `Cannot build on water or mountains`:** choose open ground closer to a completed friendly building.
- **`No open spawn point`:** move units away from the War Factory and try again.
- **`BLACKOUT`:** build another Power Plant so supply meets demand.

## Music and project files

Music plays automatically and changes with combat. Short periods of silence can be normal; see [the music guide](assets/music/README.md) for the track rules. You can change `MUSIC_VOLUME` in `config.py`.

- `main.py`: starts the game and handles the main loop.
- `game.py`, `entities.py`, and `ai.py`: game rules, objects, and computer opponent.
- `ui.py`: the interface and drawing code.
- `terrain.py` and `pathing.py`: the map, obstacles, and the project's own pathfinding.
- `config.py`: unit statistics, building costs, and other settings.
- `assets/`: the images and music used by the game.
