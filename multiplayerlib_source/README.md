# MultiplayerLib

MultiplayerLib is a lightweight UDP networking library designed for simple real-time multiplayer games. It provides a minimal, easy-to-integrate API for fast client-server communication with optional compression and encryption.

source code can be found [here](https://github.com/griffingreat1/MultiplayerLib)
---

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start-example)
- [Architecture Overview](#architecture-overview)
- [API Reference](#api-reference)
- [Packet Examples](#packet-examples)
- [Troubleshooting](#troubleshooting--tips)
- [Security Notes](#security-notes)
- [Contributors](#contributors)

---

## Features

- UDP networking for low-latency gameplay
- Multi-client server support
- Real-time state synchronization
- Optional packet compression using zlib
- Optional encryption using Fernet (AES) + PBKDF2 key derivation
- JSON-based packet formatting (human readable)
- Background threaded receive loop
- Safe send/receive queue system
- Minimal API surface: `NetworkManager`, `EncryptionManager`

---

## Installation

run the install command to install the package

```pip install multiplayerlib```

---

## Quick Start Example

### Host (Server)

```py
mgr = NetworkManager(
    is_host=True,
    base_port=5000,
    use_compression=True,
    use_encryption=False
)
mgr.start()
```

### Client

```py
mgr = NetworkManager(
    is_host=False,
    peer_ip="1.2.3.4",
    base_port=5000,
    use_compression=True,
    use_encryption=False
)
mgr.start()
```

### Sending / Receiving

```py
mgr.safe_send({
    "type": "playerdata",
    "position": {"x": 10, "y": 20, "rotation": 0},
    "health": 100
})

msg = mgr.safe_receive()
if msg:
    # handle decoded packet
    pass
```

---

## Architecture Overview

- The system follows a **client-server UDP model**:
  - One host acts as the server
  - Multiple clients can connect and send packets
- The server broadcasts received packets to all connected clients
- Each client sends state updates to the server

### Networking Flow

1. Client sends packet → Server receives
2. Server updates peer registry (heartbeats)
3. Server broadcasts packet to all other clients
4. Clients receive and process updates via `incoming_queue`

### Design Notes

- UDP is used for low latency (no built-in reliability)
- Packet delivery is not guaranteed
- Ordering is not enforced
- Designed for frequent state updates (position, actions, etc.)

---

## API Reference

### NetworkManager

#### Constructor
```py
NetworkManager(
    is_host=True,
    peer_ip=None,
    base_port=5000,
    use_compression=True,
    use_encryption=False,
    encryption_key=DEFAULT_KEY,
    encryption_salt=DEFAULT_SALT
)
```

#### Methods

- `start()`
  Starts background receive and peer cleanup threads.

- `safe_send(data: dict)`
  Sends a packet to all connected peers (server) or to the host (client).

- `safe_receive() -> dict | None`
  Non-blocking receive from internal queue.

- `close()`
  Stops networking and closes socket.

---

### Packet Pipeline

Outgoing:
```
dict → JSON → compress (optional) → encrypt (optional) → UDP packet
```

Incoming:
```
UDP packet → decrypt → decompress → JSON decode → dict
```

---

### EncryptionManager

- Uses PBKDF2-derived key + Fernet encryption
- Requires identical key/salt on both sides
- Encrypt/decrypt operates on bytes

---

## Packet Examples

Common patterns used in games:

### Player State
```json
{
  "type": "playerdata",
  "position": {
    "x": 640,
    "y": 360,
    "rotation": 1.57
  },
  "health": 100
}
```

### Action Event
```json
{
  "type": "shoot",
  "pos": [x, y],
  "vec": [vx, vy],
  "timestamp": 1234567890.0
}
```

### Disconnect
```json
{
  "type": "quit"
}
```

---


## Troubleshooting & Tips

- If bind fails, ensure the port is not in use
- If packets are missing, remember UDP does not guarantee delivery
- If encryption fails, ensure:
  - same key
  - same salt
  - same `use_encryption` setting
- Keep packets small (UDP safe size ~1–1.5KB recommended)

---

## Security Notes

- Default keys are for development only
- Always generate secure keys for real applications
- Treat UDP as **insecure transport unless encrypted**

---

## Contributors

griffingreat1
---

## License

MIT License — see [LICENSE](../LICENSE)