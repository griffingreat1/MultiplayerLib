# this file is part of MultiplayerLib, which is under an MIT license.
# see LICENSE file at root of this repository for details.

"""
Network utilities and a NetworkManager for peer-to-peer UDP communication.

Provides helpers for encoding/decoding messages, optional compression and
encryption, and a simple API for sending/receiving JSON-serializable packets.
"""

import random
import sys

import orjson
import socket
import threading
import time
from multiplayerlib.NetworkConstants import *
from multiplayerlib.EncryptionManager import EncryptionManager
from multiplayerlib.MultiplayerLibExceptions import *
import zlib
import logging
from pathlib import Path
from queue import Queue
import traceback

class Peer():
    _registry = {}
    _registry_lock = threading.Lock()
    def __init__(self,address):
        self.address = address
        self._latestPacketTime = time.time()
    
    def _heartbeat(self):
        self._latestPacketTime = time.time()
    
    def _get_is_alive(self):
        return time.time()-self._latestPacketTime < PEER_TIMEOUT
    
    def get_address(self):
        return self.address

    @classmethod
    def getInstance(cls, value):
        with cls._registry_lock:
            instance = cls._registry.get(value)
            if instance is None:
                instance = cls(value)
                cls._registry[value] = instance
            return instance

    @classmethod
    def update_registry(cls):
        with cls._registry_lock:
            cls._registry = {
                address: instance
                for address, instance in cls._registry.items()
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
        self._should_log = enable_logs
        self._logQueue = Queue()
        if enable_logs:
            log_file = Path(f"{log_file_name}_Latest.log")
            destination_file = Path(f"{log_file_name}_Old.log")
            if log_file.is_file():
                log_file.replace(destination_file)
            self._logger = logging.getLogger("MultiplayerLibLogger")
            self._logger.setLevel(logging.DEBUG)
            self._logger_console_handler = logging.StreamHandler()
            self._logger_file_handler = logging.FileHandler(f"{log_file_name}_Latest.log")
            self._logger_console_handler.setLevel(logging.WARNING)
            self._logger_file_handler.setLevel(logging.DEBUG)
            self._logger_formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
            self._logger_console_handler.setFormatter(self._logger_formatter)
            self._logger_file_handler.setFormatter(self._logger_formatter)
            self._logger.addHandler(self._logger_console_handler)
            self._logger.addHandler(self._logger_file_handler)
            self._logging_thread = threading.Thread(target=self._log_worker,daemon=True).start()

            
        if use_encryption:
            self._encryption_manager = EncryptionManager(encryption_key.encode(),encryption_salt)
            original_msg = get_sample_packet_string()
            enc_test_msg = self._encryption_manager.encrypt(zlib.compress(orjson.dumps(get_sample_packet_string())))
            unenc_test_msg = orjson.loads(zlib.decompress(self._encryption_manager.decrypt(enc_test_msg)))
            if self._should_log:
                self._logQueue.put_nowait((logging.DEBUG,f"encryption is working: {original_msg==unenc_test_msg}"))

        self._compress_packets = use_compression
        self._use_encryption = use_encryption

        self.is_host = is_host
        self.peer_ip = peer_ip
        
        self.local_port = base_port if is_host else base_port + random.randint(1,10)
        self.peer_port = base_port + 1 if is_host else base_port

        self.peer_addr = None if is_host else (peer_ip,self.peer_port)
        self._banned_addr = set()
        self._banned_addr_lock = threading.Lock()

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 32768)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 32768)
        self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0x10)
        self._sock.settimeout(0.5)

        try:
            self._sock.bind(("",self.local_port))
            print(f"Socket bound to {socket.gethostbyname(socket.gethostname())}:{self.local_port}")
            if self._should_log:
                self._logQueue.put_nowait((logging.DEBUG,f"Socket bound to {socket.gethostbyname(socket.gethostname())}:{self.local_port}"))
        except OSError as e:
            if self._should_log:
                self._logQueue.put_nowait((
                    logging.CRITICAL,
                    f"Socket bind failed on port {self.local_port}:\n{traceback.format_exc()}"
                ))

            raise SocketBindError(
                f"Failed to bind socket to port {self.local_port}"
            ) from e
        
        self.running = False
        self._incoming_queue = Queue()
    
    def start(self) -> None:
        """
        Start the receiver loop in a background thread.
        """
        self.running = True
        threading.Thread(
            target=self._recv_loop, 
            daemon=True
        ).start()

        threading.Thread(
            target=self._peer_cleanup_loop,
            daemon=True
        ).start()
        if self._should_log:
            self._logQueue.put_nowait((logging.INFO,"NetworkManager started."))

    def _peer_cleanup_loop(self):
        """
        Periodically remove timed-out peers.
        """
        while self.running:
            Peer.update_registry()
            time.sleep(1)

    def _recv_loop(self) -> None:
        """
        Continuously receive packets and decode them into the incoming queue.
        """
        while self.running:
            try:
                data,addr = self._sock.recvfrom(BUFFER_SIZE)
                if self.is_host:
                    with self._banned_addr_lock:
                        banned = addr in self._banned_addr

                    if banned:
                        continue
                    peer = Peer.getInstance(addr)
                    peer._heartbeat()
                    with Peer._registry_lock:
                        peers = list(Peer._registry.items())

                    for address, peer in peers:
                        if address != addr:
                            self._sock.sendto(data, address)
                try:
                    msg = self._decode_message(data)
                    self._incoming_queue.put(msg)
                except Exception:
                    if self._should_log:
                        self._logQueue.put_nowait((logging.ERROR,traceback.format_exc()))
            except TimeoutError:
                time.sleep(0.01)
            except Exception:
                if self._should_log:
                    self._logQueue.put_nowait((logging.ERROR,traceback.format_exc()))

    def ban_addr(self, addr) -> bool:
        """IP bans specified address. returns True if successful, False if called on non host instance."""
        if not self.is_host:
            return False
        try:
            with self._banned_addr_lock:
                self._banned_addr.add(addr)
            return True
        except Exception:
            if self._should_log:
                self._logQueue.put_nowait((logging.ERROR,traceback.format_exc()))
            return False

    def unban_addr(self, addr) -> bool:
        """IP unbans specified address. returns True if successful, False if called on non host instance."""
        if not self.is_host:
            return False
        try:
            with self._banned_addr_lock:
                self._banned_addr.remove(addr)
            return True
        except Exception:
            if self._should_log:
                self._logQueue.put_nowait((logging.ERROR,traceback.format_exc()))
            return False

    def safe_receive(self) -> JSONValue | None:
        """
        Retrieve the next parsed packet from the incoming queue in a non-blocking way.
        """
        try:
            return self._incoming_queue.get_nowait()
        except:
            return None
    
    def _decode_message(self, message_encoded: bytes) -> JSONValue:
        """
        Decode a raw packet into a Python object.
        """
        if self._use_encryption:
            message_encoded = self._encryption_manager.decrypt(message_encoded)
        if self._compress_packets:
            message_encoded = zlib.decompress(message_encoded)
        message = orjson.loads(message_encoded)
        return message

    def _prepare_message(self, data: JSONValue) -> bytes:
        """
        Prepare a Python object for sending over the network.
        """
        message_encoded = orjson.dumps(data)
        if self._compress_packets:
            message_encoded = zlib.compress(message_encoded)
        if self._use_encryption:
            message_encoded = self._encryption_manager.encrypt(message_encoded)
        return message_encoded

    def safe_send(self, data: JSONValue) -> None:
        """
        Send a data packet to the currently known peer address.
        :param data: Data to send. Must consist only of JSON-compatible values:
        None, bool, int, float, str, lists, and dictionaries with string keys.
        Lists and dictionaries may contain only JSON-compatible values.
        """
        message = self._prepare_message(data)
        if self.is_host:
            with Peer._registry_lock:
                peers = list(Peer._registry.items())

            for address, peer in peers:
                try:
                    self._sock.sendto(message, address)
                except Exception:
                    if self._should_log:
                        self._logQueue.put_nowait((logging.ERROR,traceback.format_exc()))
        else:
            if self.peer_addr:
                try:
                    self._sock.sendto(message, self.peer_addr)
                except Exception:
                    if self._should_log:
                        self._logQueue.put_nowait((logging.ERROR,traceback.format_exc()))

    def close(self) -> None:
        """
        Stop the receive loop and close the underlying socket.
        """
        self.running = False
        try:
            self._sock.close()
            self._logQueue.put_nowait((logging.INFO,"NetworkManager Closed"))
            self._logQueue.put_nowait(None)
        except Exception:
            pass

    def _log_worker(self):
        while True:
            level,message = self._logQueue.get()
            if message is None:
                break
            
            self._logger.log(level,message)

def get_sample_packet_string() -> dict:
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