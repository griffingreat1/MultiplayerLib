# this file is part of MultiplayerLib, which is under an MIT license.
# see LICENSE file at root of this repository for details.

"""
Network utilities and a NetworkManager for peer-to-peer UDP communication.

Provides helpers for encoding/decoding messages, optional compression and
encryption, and a simple API for sending/receiving JSON-serializable packets.
"""

import random

import orjson
import socket
import threading
import time
from multiplayerlib.NetworkConstants import *
from multiplayerlib.EncryptionManager import EncryptionManager
import zlib
import logging
from pathlib import Path
from queue import Queue
import traceback

class Peer():
    registry = {}
    registry_lock = threading.Lock()
    def __init__(self,address):
        self.address = address
        self.latestPacketTime = time.time()
    
    def heartbeat(self):
        self.latestPacketTime = time.time()
    
    def get_is_alive(self):
        return time.time()-self.latestPacketTime < PEER_TIMEOUT
    
    def get_address(self):
        return self.address

    @classmethod
    def getInstance(cls, value):
        with cls.registry_lock:
            instance = cls.registry.get(value)
            if instance is None:
                instance = cls(value)
                cls.registry[value] = instance
            return instance

    @classmethod
    def update_registry(cls):
        with cls.registry_lock:
            cls.registry = {
                address: instance
                for address, instance in cls.registry.items()
                if instance.get_is_alive()
            }

class NetworkManager:
    """
    High-level manager for UDP networking.

    Handles socket setup, optional compression and encryption of packets, and
    provides a background receiving loop to accumulate incoming messages.
    """
    def __init__(self, is_host=True, peer_ip=None, base_port=DEFAULT_PORT, use_compression=False, use_encryption=False, encryption_key=DEFAULT_KEY, encryption_salt=DEFAULT_SALT, enable_logs = False, log_file_name="MultiplayerLib_Logs") -> None:
        """
        Network Manager
        
        :param is_host: host server or connect to server
        :param peer_ip: ip address of peer (only required if client is NOT the server host)
        :param base_port: the base port for the server. server hosts recv on this port and client hosts recv on base_port + 1. client sends to base_port and server sends to base_port + 1
        :param use_compression: if true, packets will be compressed. this allows for reduced size of packets. defaults to true. (most UDP packets should be small enough that this isnt needed)
        :param use_encryption: if true, packets will be encrypted before sending.
        :param enable_logs: if true, MultiplayerLib will create a log file to log networking events/exceptions. MultiplayerLib by default keeps the latest 2 logs.
        :param log_file_name: the file name to use for log file. this file name will be followed by a suffix to denote which log is more recent.
        """
        self.should_log = enable_logs
        self.logQueue = Queue()
        if enable_logs:
            log_file = Path(f"{log_file_name}_Latest.log")
            destination_file = Path(f"{log_file_name}_Old.log")
            if log_file.is_file():
                log_file.replace(destination_file)
            self.logger = logging.getLogger("MultiplayerLibLogger")
            self.logger.setLevel(logging.DEBUG)
            self.logger_console_handler = logging.StreamHandler()
            self.logger_file_handler = logging.FileHandler(f"{log_file_name}_Latest.log")
            self.logger_console_handler.setLevel(logging.WARNING)
            self.logger_file_handler.setLevel(logging.DEBUG)
            self.logger_formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
            self.logger_console_handler.setFormatter(self.logger_formatter)
            self.logger_file_handler.setFormatter(self.logger_formatter)
            self.logger.addHandler(self.logger_console_handler)
            self.logger.addHandler(self.logger_file_handler)
            self.loggingThread = threading.Thread(target=self.logWorker,daemon=True).start()

            
        if use_encryption:
            self.encryptionManager = EncryptionManager(encryption_key.encode(),encryption_salt)
            originalMessage = getSamplePacketString()
            encryptedTestMessage = self.encryptionManager.encrypt(zlib.compress(orjson.dumps(getSamplePacketString())))
            decryptedTestMessage = orjson.loads(zlib.decompress(self.encryptionManager.decrypt(encryptedTestMessage)))
            if self.should_log:
                self.logger.info(f"encryption is working: {originalMessage==decryptedTestMessage}")

        self.compress_packets = use_compression
        self.use_encryption = use_encryption

        self.is_host = is_host
        self.peer_ip = peer_ip
        
        self.local_port = base_port if is_host else base_port + random.randint(1,10)
        self.peer_port = base_port + 1 if is_host else base_port

        self.peer_addr = None if is_host else (peer_ip,self.peer_port)
        self.banned_addr = set()
        self.banned_addr_lock = threading.Lock()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 32768)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 32768)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0x10)
        self.sock.settimeout(0.5)

        try:
            self.sock.bind(("",self.local_port))
            print(f"Socket bound to {socket.gethostbyname(socket.gethostname())}:{self.local_port}")
            if self.should_log:
                self.logger.debug(f"Socket bound to {socket.gethostbyname(socket.gethostname())}:{self.local_port}")
        except OSError as e:
            print(f"Socket bind failed on port {self.local_port}: {e}")
            if self.should_log:
                self.logger.exception(e)
        
        self.running = False
        self.incoming_queue = Queue()
    
    def start(self) -> None:
        """
        Start the receiver loop in a background thread.
        """
        self.running = True
        threading.Thread(
            target=self.recv_loop, 
            daemon=True
        ).start()

        threading.Thread(
            target=self.peer_cleanup_loop,
            daemon=True
        ).start()
        if self.should_log:
            self.logger.info("NetworkManager started.")

    def peer_cleanup_loop(self):
        """
        Periodically remove timed-out peers.
        """
        while self.running:
            Peer.update_registry()
            time.sleep(1)

    def recv_loop(self) -> None:
        """
        Continuously receive packets and decode them into the incoming queue.
        """
        while self.running:
            try:
                data,addr = self.sock.recvfrom(BUFFER_SIZE)
                if self.is_host:
                    with self.banned_addr_lock:
                        banned = addr in self.banned_addr

                    if banned:
                        continue
                    peer = Peer.getInstance(addr)
                    peer.heartbeat()
                    with Peer.registry_lock:
                        peers = list(Peer.registry.items())

                    for address, peer in peers:
                        if address != addr:
                            self.sock.sendto(data, address)
                try:
                    msg = self.decode_message(data)
                    self.incoming_queue.put(msg)
                except Exception:
                    if self.should_log:
                        self.logQueue.put_nowait(traceback.format_exc())
            except TimeoutError:
                time.sleep(0.01)
            except Exception:
                if self.should_log:
                    self.logQueue.put_nowait(traceback.format_exc())

    def ban_addr(self, addr) -> bool:
        """IP bans specified address. returns True if successful, False if called on non host instance."""
        if not self.is_host:
            return False
        try:
            with self.banned_addr_lock:
                self.banned_addr.add(addr)
            return True
        except Exception:
            if self.should_log:
                self.logQueue.put_nowait(traceback.format_exc())
            return False

    def unban_addr(self, addr) -> bool:
        """IP unbans specified address. returns True if successful, False if called on non host instance."""
        if not self.is_host:
            return False
        try:
            with self.banned_addr_lock:
                self.banned_addr.remove(addr)
            return True
        except Exception:
            if self.should_log:
                self.logQueue.put_nowait(traceback.format_exc())
            return False

    def safe_receive(self) -> dict | None:
        """
        Retrieve the next parsed packet from the incoming queue in a non-blocking way.
        """
        try:
            return self.incoming_queue.get_nowait()
        except:
            return None
    
    def decode_message(self, message_encoded: bytes) -> dict:
        """
        Decode a raw packet into a Python object.
        """
        if self.use_encryption:
            message_encoded = self.encryptionManager.decrypt(message_encoded)
        if self.compress_packets:
            message_encoded = zlib.decompress(message_encoded)
        message = orjson.loads(message_encoded)
        return message

    def prepare_message(self, data: dict) -> bytes:
        """
        Prepare a Python object for sending over the network.
        """
        message_encoded = orjson.dumps(data)
        if self.compress_packets:
            message_encoded = zlib.compress(message_encoded)
        if self.use_encryption:
            message_encoded = self.encryptionManager.encrypt(message_encoded)
        return message_encoded

    def safe_send(self, data: dict) -> None:
        """
        Send a data packet to the currently known peer address.
        """
        message = self.prepare_message(data)
        if self.is_host:
            with Peer.registry_lock:
                peers = list(Peer.registry.items())

            for address, peer in peers:
                try:
                    self.sock.sendto(message, address)
                except Exception:
                    if self.should_log:
                        self.logQueue.put_nowait(traceback.format_exc())
        else:
            if self.peer_addr:
                try:
                    self.sock.sendto(message, self.peer_addr)
                except Exception:
                    if self.should_log:
                        self.logQueue.put_nowait(traceback.format_exc())

    def close(self) -> None:
        """
        Stop the receive loop and close the underlying socket.
        """
        self.running = False
        try:
            self.sock.close()
            self.logQueue.put_nowait(None)
        except Exception:
            pass

    def logWorker(self):
        while True:
            message = self.logQueue.get()
            if message is None:
                break

            self.logger.error(message)

def getSamplePacketString() -> dict:
    """
    Returns a basic example of a packet in a dictionary structure.
    """
    data = {
        "type":"playerdata",
        "packetNum":random.randint(0,100),
        "position":{
            "x":random.randint(0,600),
            "y":random.randint(0,600),
            "rotation":random.uniform(0,6.28)
        },
        "velocity":[random.randint(0,5),random.randint(0,5)],
        "health":random.randint(0,100),
        "timestamp":time.time(),
        "deaths":random.randint(0,100),
        "ID":random.randint(0,1000)
    }
    return data