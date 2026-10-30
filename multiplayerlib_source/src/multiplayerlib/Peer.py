# this file is part of MultiplayerLib, which is under an MIT license.
# see LICENSE file at root of this repository for details.
import threading
import time
from multiplayerlib.NetworkConstants import *

class Peer():
    """
    Helper class for managing connected peers. It is highly recommended not to modify or call this class in your own code unless you are confident that you know what you are doing.
    """
    _registry = {}
    _registry_lock = threading.Lock()
    def __init__(self,address,peer_timeout=MPL_DEFAULT_PEER_TIMEOUT):
        self.address = address
        self._latestPacketTime = time.time()
        self._PEER_TIMEOUT = peer_timeout
    
    def _heartbeat(self):
        self._latestPacketTime = time.time()
    
    def _get_is_alive(self):
        return time.time()-self._latestPacketTime < self._PEER_TIMEOUT
    
    def get_address(self):
        return self.address

    @classmethod
    def getInstance(cls, value, peer_timeout):
        with cls._registry_lock:
            instance = cls._registry.get(value)
            if instance is None:
                instance = cls(value,peer_timeout)
                cls._registry[value] = instance
            return instance

    @classmethod
    def update_registry(cls):
        with cls._registry_lock:
            cls._registry = {
                address: instance
                for address, instance in cls._registry.items()
                if instance._get_is_alive()
            }