# MultiplayerLib

MultiplayerLib is a lightweight and extensible UDP networking library designed for real-time multiplayer games. It provides simple, secure, and fast peer-to-peer communication with optional encryption and packet compression. The API is intentionally minimal to keep integration easy while still supporting smooth gameplay and synchronized state.

### ✨ Features

- 🚀 UDP networking for low-latency gameplay

- 🔁 Host ↔ Client peer communication

- 🗜️ Optional packet compression using zlib

- 🔐 Optional encryption using Fernet (AES)

- 📦 JSON-based packet formatting

- 🧵 Background threaded receive loop

- 🛡️ Safe send/receive queue

- 🎯 Designed for real-time state sync

- 🎮 Includes example packet structure

## 🕹 Demo Game

### Included demo features:

- real-time position sync

- projectile events

- latency measurement

- blood & particle effects

- optional encryption

- custom physics

The demo is written using pygame and showcases practical usage.

## ❗ Current Limitations

- optimized for 1v1 (two peers)

- UDP without reliability layer

- no automatic NAT traversal

## Planned:

- multi-client support

- packet ordering & reliability

# 🤝 Contributing

Contributions and merge requests are welcome!
Feel free to fork, extend, or integrate MultiplayerLib into your own game.

# ❤️ Author

Created by griffingreat1
Designed for real-time multiplayer Python game development.