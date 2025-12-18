# MultiplayerLib — MIT License
# Copyright (c) 2025 griffingreat1
#
# This file is part of MultiplayerLib.
# You may use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of this file under the terms of the MIT License.
# See the LICENSE file in the repository root for full license text.
from MultiplayerLib.NetworkConstants import *
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import sys
import zlib

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
    
    def encrypt(self,bytesObject):
        return self.encrypter.encrypt(bytesObject)

    def decrypt(self,bytesObject):
        return self.encrypter.decrypt(bytesObject)
