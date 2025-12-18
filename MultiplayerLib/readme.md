# MultiplayerLib

MultiplayerLib is a lightweight UDP networking library intended for simple real-time peer-to-peer games. It aims to be minimal and easy to integrate while providing optional packet compression and encryption for reliability and privacy.

---
## Table of Contents
- [Features](#✨-features)
- [Installation](#📦-installation)
- [Quick Start](#quick-start-example)
- [API Reference](#api-reference)
- [Packet Examples](#packet-examples-and-typical-usage-in-a-game)
- [Troubleshooting](#troubleshooting--tips)
- [Security](#security-notes)
- [Contributing](#contributing)

## ✨ Features

- 🚀 UDP networking for low-latency gameplay
- 🔁 Host ↔ Client peer communication (simple 1:1 pairing)
- 🗜️ Optional packet compression using zlib
- 🔐 Optional encryption using Fernet (AES) + PBKDF2 key derivation
- 📦 JSON-based packet formatting (human readable)
- 🧵 Background threaded receive loop and safe send/receive queue
- 🔧 Small, explicit API surface: `NetworkManager`, `EncryptionManager`

---

## 📦 Installation

Copy the `MultiplayerLib` folder into your project and import it as a normal Python package (e.g. `from MultiplayerLib import NetworkManager`).

---

## Quick start (example)

This shows a short example of how to create a host or a client and start the receive loop:

```py
from MultiplayerLib.NetworkLib import NetworkManager

# host:
mgr = NetworkManager(is_host=True, base_port=5000, use_compression=True, use_encryption=False)
mgr.start()  # spawns the receive thread

# client:
mgr = NetworkManager(is_host=False, peer_ip='1.2.3.4', base_port=5000, use_compression=True, use_encryption=False)
mgr.start()

# send a packet once you have a peer address (host learns client addr on first receive):
mgr.safe_send({ 'type': 'playerdata', 'position': {'x': 10, 'y': 20, 'rotation': 0}, 'health': 100 })

# poll incoming packets safely anywhere in your game loop:
msg = mgr.safe_receive()
if msg:
    # handle message (it's already decoded and JSON-parsed)
    pass
```

---

## How it works / Design notes

- Ports: if `is_host=True` the manager binds to `base_port`; the peer (client) binds to `base_port + 1`. The host sends to the client's port +1 and the client sends to the host's base port, so both directions are covered even with UDP.
- The manager uses a background thread (`recv_loop`) to append decoded packets to an internal `incoming_queue`. Use `safe_receive()` to pop messages off that queue.
- Packets are JSON strings by default, optionally compressed with `zlib` and/or encrypted using `Fernet` (AES). Encryption uses PBKDF2HMAC with a salt and a key string to derive a Fernet-compatible key.

---

## API Reference

### NetworkManager

Constructor: NetworkManager(is_host=True, peer_ip=None, base_port=5000, use_compression=True, use_encryption=True, encryption_key=DEFAULT_KEY, encryption_salt=DEFAULT_SALT)

Key attributes & methods:
- `start()` — starts the background receive thread (`recv_loop`).
- `safe_receive()` — returns next decoded packet (a dict) or `None` if empty.
- `safe_send(data)` — sends a dictionary to the last-known peer address. If you are the client you must pass `peer_ip` to the constructor; a host will learn the peer address when the client first sends a packet.
- `close()` — stops the receive thread and closes the socket.

Behavior details:
- Incoming bytes are processed by `decode_message` which performs decryption (if enabled), decompression (if enabled), UTF-8 decode, and `json.loads`.
- Outgoing dicts are processed by `prepare_message` which does `json.dumps`, UTF-8 encode then optional compression and encryption.
- Socket uses UDP (`socket.SOCK_DGRAM`) with a short recv timeout.

### EncryptionManager

- Internal helper class used when `use_encryption=True`.
- Derives a 32-byte key via PBKDF2HMAC (SHA-256) and converts to a Fernet key.
- `encrypt(bytesObject)` and `decrypt(bytesObject)` wrappers around `Fernet`.
- Important: encryption must match on both endpoints (same key and salt) or messages won't decrypt.

---

## Packet examples and typical usage in a game (based on Example_game/basicMultiplayerGame.py)

Recommended packet types used in the example game:

- `playerdata` — used to sync position & rotation & health
  {
    "type": "playerdata",
    "position": { "x": 640, "y": 360, "rotation": 1.57 },
    "health": 100
  }

- `shoot` — notify the other peer a shot has occurred
  {
    "type": "shoot",
    "pos": [x, y],
    "vec": [vx, vy],
    "timestamp": 1234567890.0
  }

- `quit` — graceful disconnect notification
  { "type": "quit" }

Integration pattern used by the example game:
- For position updates the example either sends a position packet each game loop or runs a dedicated thread that sends at `POSITIONUPDATEINTERVAL` (default 1/30s).
- A background receiver thread keeps calling `safe_receive()` and starts a thread to handle each packet (`update_conn_with_packet`) to avoid blocking the receiver.
- When sending events (like `shoot`) the game sends a short event packet and the other side constructs projectiles from the received data.

---

## Important constants

These are defined in `NetworkConstants.py`:
- `BUFFER_SIZE = 4096` — max UDP receive buffer size
- `DEFAULT_PORT = 5000` — default base port
- `DEFAULT_KEY` / `DEFAULT_SALT` — defaults used for encryption key derivation
- `POSITIONUPDATEINTERVAL = 1/30` — frequency for background position updates
- `POSITION_UPDATE_PACKET_IN_MAIN_LOOP = False` — toggle to send position updates directly from the main loop

---

## Troubleshooting & tips

- If `sock.bind(...)` raises `OSError`, make sure the port is free and your firewall allows UDP traffic.
- If encryption seems to fail, confirm both peers use the same `encryption_key` and `encryption_salt` and use `use_encryption=True` on both sides.
- Keep messages small — UDP has practical limits; use compression if you need to reduce payload size.
- Test locally first (host and client on the same machine but different ports) to ensure basic flow works before testing over LAN or the internet.

---

## Security Notes

- Default key/salt values are provided for convenience. **In production, generate or prompt the user for a secure key and a unique salt.**
- Use a sufficiently random string for the `encryption_key` and a unique integer for the salt to ensure proper encryption.

---

## Contributing

Small and focused PRs welcome — example: add a new packet type, add tests, or improve `NetworkManager` logging and error handling.