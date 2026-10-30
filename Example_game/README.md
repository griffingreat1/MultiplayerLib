# Demo Game
 
A small top-down multiplayer shooter that serves as an example implementation of **MultiplayerLib**. It is written with pygame and shows how the library is used in a real, playable game.
 
## Features
 
### Multiplayer features (the point of the demo)
 
- **Real-time player synchronization:** position, aim direction, health and death count are sent about 20 times per second. Remote players are smoothly interpolated so they don't jitter between updates.
- **Latency measurement:** each remote player's ping is displayed under them.
- **Projectile events with latency correction:** shots are sent as events, and the receiving client fast-forwards the bullet by the packet's latency so it lands where it would have on the shooter's screen.
- **Optional encryption:** choose a key and salt at startup, or use the library defaults.
- **No separate server program:** one player hosts from inside the game, and everyone else connects to them as a client.
- **Disconnect handling:** a peer that stops sending packets for 5 seconds is removed from the game. Closing the host's game also closes connected clients.
### Gameplay features
 
- **WASD movement** with a **sprint** that drains stamina and recharges after a short delay.
- **Mouse aiming and shooting** with a 6-round magazine, 480 RPM fire rate and 1.5 second reload.
- **Headshots:** a head hit deals 2.5x damage (12 damage for a body shot, 30 for a headshot).
- **Respawning:** at 0 health you respawn at a random spot with full health.
- **Blood and particle effects:** hits spray blood in the direction of the shot, and headshots spray more.
- **Low-health vignette:** a red vignette creeps in from the screen edges as your health drops below 50.
- **HUD:** health is shown at the bottom left, ammo (or "reloading...") at the bottom right.
You are the green circle, and other players are red.
 
## Requirements
 
- Python 3.10 or newer
- `pygame` - tested with version 2.6.1
- `multiplayerlib`
- `pip install -r requirements.txt`

## How to run
 
Run `basicMultiplayerGame.py` from this directory:
 
```
python basicMultiplayerGame.py
```
 
The program prompts you for configuration options in the terminal. **Run the game once for each player.**
 
1. **One player must be the host.** To host, leave the *peer ip address* prompt blank.
2. **The host must be running (game window open) before any client tries to connect.**
3. **Clients enter the host's IP address** at the *peer ip address* prompt:
   - If the host is running on your own machine, use `127.0.0.1`.
   - If the host is on a different machine, use that machine's IP address. Make sure the host's firewall allows the connection.
### Encryption
 
Encryption is optional, and it is faster and lower latency without it.
 
- The host is asked whether to use encryption. Clients are asked whether the host is using it, and **must answer the same way.**
- If encryption is on, you are asked for an **encryption key** (text) and a **salt** (an integer). Leave either blank to use the library default.
- **The key and salt must be identical on the host and every client**, or the players won't be able to communicate. If you leave an input blank, tell the other players to leave theirs blank too.
## Controls
 
| Input | Action |
| --- | --- |
| `W` `A` `S` `D` | Move |
| `Left Shift` (hold) | Sprint (uses stamina) |
| Mouse | Aim |
| Left click | Shoot |
| `R` | Reload |
| `Esc` or close window | Quit |
 
## Configuration
 
Gameplay and networking values such as weapon stats, player speed, window size, position update rate and the optional motion blur effect are defined in `GameUtils/GameLib/GameConstants.py`.
 
## Project layout
 
```
basicMultiplayerGame.py      # Entry point: networking setup, packet handling, game loop
GameUtils/
  GameLib/
    GameConstants.py         # Tunable gameplay and networking constants
    Player.py                # Local Player and remote ConnectedPlayer classes
    Projectile.py            # Bullets
    ParticleManager.py       # Blood and particle effects
    ScreenEffects.py         # Low-health vignette and motion blur
```
 
`basicMultiplayerGame.py` is the best place to start if you want to see how the library is used. It shows how to create the `NetworkManager`, send packets, and receive and handle them.

To see how NetworkManager actually works, be sure to check out the [library documentation](../multiplayerlib_source/)