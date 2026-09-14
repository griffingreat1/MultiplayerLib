# this file is part of MultiplayerLib, which is under an MIT license.
# see LICENSE file at root of this repository for details.

from multiplayerlib.NetworkConstants import *
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import sys

class EncryptionManager:
    def __init__(self,key,salt):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.to_bytes(16,sys.byteorder),
            iterations=1_000_000,
        )
        self.key = base64.urlsafe_b64encode(kdf.derive(key))
        self.encrypter = Fernet(self.key)
    
    def _encrypt(self,bytesObject):
        return self.encrypter.encrypt(bytesObject)

    def _decrypt(self,bytesObject):
        return self.encrypter.decrypt(bytesObject)
