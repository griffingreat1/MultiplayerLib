# MultiplayerLib

MultiplayerLib is a lightweight and extensible UDP networking library designed for real-time multiplayer games. It provides simple, secure, and fast peer-to-peer communication with optional encryption and packet compression. The API is intentionally minimal to keep integration easy while still supporting smooth gameplay and synchronized state.

---

## ✨ Features

- 🚀 UDP networking for low-latency gameplay  
- 🔁 Host ↔ Client peer communication  
- 🗜️ Optional packet compression using zlib  
- 🔐 Optional encryption using Fernet (AES)  
- 📦 JSON-based packet formatting  
- 🧵 Background threaded receive loop  
- 🛡️ Safe send/receive queue  
- 🎯 Designed for real-time state sync  
- 🎮 Includes example packet structure  

---

## 📦 Installation

Copy the `MultiplayerLib` directory into your project.

## recommended packet structure:
{
  "type": "playerdata",
  "position": { "x": 640, "y": 360, "rotation": 1.57 },
  "health": 100
}