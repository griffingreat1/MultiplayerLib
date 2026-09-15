class MultiplayerLibError(Exception):
    pass


class NetworkError(MultiplayerLibError):
    pass


class SocketBindError(NetworkError):
    pass