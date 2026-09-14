# MultiplayerLib

MultiplayerLib is a lightweight and extensible UDP networking library designed for real-time multiplayer games. It provides simple, secure, and fast client-server communication with optional encryption and packet compression. The API is intentionally minimal to keep integration easy while still supporting smooth gameplay and synchronized state across multiple connected players.

for MultiplayerLib specific docs, go [here](multiplayerlib_source/README.md)

### ✨ Features

- 🚀 UDP networking for low-latency gameplay

- 👥 Multi-client server support

- 🔄 Real-time state synchronization

- 🗜️ Optional packet compression using zlib

- 🔐 Optional encryption using Fernet (AES)

- 📦 JSON-based packet formatting

- 🧵 Background threaded receive loop

- 🛡️ Safe send/receive queue system

- 🎯 Designed for fast-paced multiplayer games

- 🎮 Includes example packet structure

## 🕹 Demo Game

### Included demo features:

- real-time player synchronization

- projectile events

- latency measurement

- blood & particle effects

- optional encryption

- custom physics

- no separate application to run the server, one application can run it all.

The demo is written using pygame and showcases practical real-world usage of the library.

## Current Limitations

- no automatic NAT traversal

- limited server-side authority/game-state validation

## Planned Features

- dedicated server tooling

- improved connection management

- optional authoritative server systems

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

# Contributing

Contributions and merge requests are welcome!  
Feel free to fork, extend, or integrate MultiplayerLib into your own projects.

# Author

Created by griffingreat1  
Designed for real-time multiplayer Python game development.