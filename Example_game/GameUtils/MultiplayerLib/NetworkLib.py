# MultiplayerLib — MIT License
# Copyright (c) 2025 griffingreat1
#
# This file is part of MultiplayerLib.
# You may use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of this file under the terms of the MIT License.
# See the LICENSE file in the repository root for full license text.
import json
import socket
import threading
import time
from GameUtils.MultiplayerLib.NetworkConstants import *
from GameUtils.MultiplayerLib.EncryptionManager import EncryptionManager
import zlib

class NetworkManager:
    """
    High-level manager for peer-to-peer UDP networking.

    Handles socket setup, optional compression and encryption of packets, and
    provides a background receiving loop to accumulate incoming messages.
    """
    def __init__(self, is_host=True, peer_ip=None, base_port=DEFAULT_PORT, use_compression=True, use_encryption=True, encryption_key=DEFAULT_KEY, encryption_salt=DEFAULT_SALT):
        """
        Network Manager
        
        :param is_host: host server or connect to server
        :param peer_ip: ip address of peer (only required if client is NOT the server host)
        :param base_port: the base port for the server. server hosts recv on this port and client hosts recv on base_port + 1. client sends to base_port and server sends to base_port + 1
        :param use_compression: if true, packets will be compressed. this allows for reduced size of packets. defaults to true.
        :param use_encryption: if true, packets will be encrypted before sending.
        """
        if use_encryption:
            self.encryptionManager = EncryptionManager(encryption_key.encode(),encryption_salt)
            originalMessage = getSamplePacketString()
            encryptedTestMessage = self.encryptionManager.encrypt(zlib.compress(json.dumps(getSamplePacketString()).encode()))
            decryptedTestMessage = json.loads(zlib.decompress(self.encryptionManager.decrypt(encryptedTestMessage)).decode())
            print(f"encryption is working: {originalMessage==decryptedTestMessage}")

        self.compress_packets = use_compression
        self.use_encryption = use_encryption

        self.is_host = is_host
        self.peer_ip = peer_ip
        
        self.local_port = base_port if is_host else base_port + 1
        self.peer_port = base_port + 1 if is_host else base_port

        self.peer_addr = None if is_host else (peer_ip,self.peer_port)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(0.05)

        try:
            self.sock.bind(("",self.local_port))
            print(f"Socket bound to {socket.gethostbyname(socket.gethostname())}:{self.local_port}")
        except OSError as e:
            print(f"Socket bind failed on port {self.local_port}: {e}")
        
        self.running = False
        self.incoming_queue = []
    
    def start(self):
        """
        Start the receiver loop in a background thread.

        This sets the internal running flag and launches the receive loop as a
        daemon thread so it does not prevent program exit.
        """
        self.running = True
        threading.Thread(target=self.recv_loop, daemon=True).start()

    def recv_loop(self):
        """
        Continuously receive packets and decode them into the incoming queue.

        The loop runs while `self.running` is True. Incoming datagrams are
        processed by `decode_message` and appended to `incoming_queue`. If the
        instance is a host and no peer address has been set yet, the sender's
        address will be stored as the peer address.

        This method intentionally swallows transient exceptions to keep the
        receiver loop robust; callers should rely on `safe_receive` to access
        parsed messages.
        """
        while self.running:
            try:
                data,addr = self.sock.recvfrom(BUFFER_SIZE)
                if self.is_host and not self.peer_addr:
                    self.peer_addr = addr
                    print(f"Client connected: {addr}")
                try:
                    msg = self.decode_message(data)
                    self.incoming_queue.append(msg)
                except Exception:
                    # Ignore malformed packets or transient decode errors
                    pass
            except Exception:
                time.sleep(0.01)

    def safe_receive(self):
        """
        Retrieve the next parsed packet from the incoming queue in a non-blocking way.

        Returns the next available message dictionary if present, otherwise
        returns `None`. This method is safe to call from the main thread to
        poll for new messages.
        """
        if self.incoming_queue:
            return self.incoming_queue.pop(0)
        return None
    
    def decode_message(self,message_encoded:bytes):
        """
        Decode a raw packet into a Python object.

        The reverse of `prepare_message`: optionally decrypts, decompresses,
        decodes to UTF-8 string, and parses JSON into a Python object.

        :param message_encoded: Raw packet bytes received from the socket.
        :return: The decoded Python object (typically a dict) parsed from JSON.
        :raises: Exceptions from `EncryptionManager`, `zlib.decompress`, or
                 `json.loads` may propagate if the data is invalid.
        """
        if self.use_encryption:
            message_encoded = self.encryptionManager.decrypt(message_encoded)
        if self.compress_packets:
            message_encoded = zlib.decompress(message_encoded)
        message = message_encoded.decode()
        message = json.loads(message)
        return message

    def prepare_message(self,data):
        """
        Prepare a Python object for sending over the network.

        The object (typically a dict) is serialized to JSON, encoded to UTF-8,
        and then optionally compressed and/or encrypted depending on the
        manager's configuration.

        :param data: A JSON-serializable Python object to send.
        :return: The bytes payload ready to be sent via UDP.
        """
        message = json.dumps(data)
        message_encoded = message.encode()
        if self.compress_packets:
            message_encoded = zlib.compress(message_encoded)
        if self.use_encryption:
            message_encoded = self.encryptionManager.encrypt(message_encoded)
        return message_encoded

    def safe_send(self, data):
        """
        Send a data packet to the currently known peer address.

        If no peer address is known this is a no-op. The method prepares the
        message using `prepare_message` and sends it via the UDP socket. Any
        exceptions raised while sending are ignored to avoid crashing the
        caller.

        :param data: A JSON-serializable Python object to send to the peer.
        """
        if self.peer_addr:
            try:
                self.sock.sendto(self.prepare_message(data), self.peer_addr)
            except Exception:
                # Ignore send failures (e.g., network flakiness)
                pass

    def close(self):
        """
        Stop the receive loop and close the underlying socket.

        This will cause the background receive thread to exit and releases the
        system socket resource. Exceptions raised during socket close are
        suppressed.
        """
        self.running = False
        try:
            self.sock.close()
        except Exception:
            pass

def getSamplePacketString():
    """
    returns a basic example of a packet in a dictionary structure that is both computer and human readable. example presents the dictionary, with some fake values for position, rotation, and health
    """
    data = {
        "type":"playerdata",
        "position":{
            "x":640,
            "y":360,
            "rotation":1.57
        },
        "health":100
    }
    return data