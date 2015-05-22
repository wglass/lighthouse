import json
import socket


DEFAULT_PEER_PORT = 1024


class Peer(object):
    """
    This class represents a host running a lighthouse reporter.

    When a reporter script tells its discovery method that a node is up, it
    includes information about itself via this class so that writer scripts
    reading that information can coordinate their peers.

    This is helpful for HAProxy as a way to generate "peers" config stanzas
    so instances of HAProxy in a given cluster can share stick-table data.
    """

    def __init__(self, name, ip, port=None):
        self.name = name
        self.ip = ip
        self.port = port or DEFAULT_PEER_PORT

    @classmethod
    def current(cls):
        """
        Helper method for getting the current peer of whichever host we're
        running on.
        """
        name = socket.getfqdn()
        ip = socket.gethostbyname(name)

        return cls(name, ip)

    def serialize(self):
        """
        Serializes the Peer data as a simple JSON map string.
        """
        return json.dumps({
            "name": self.name,
            "ip": self.ip,
            "port": self.port
        }, sort_keys=True)

    @classmethod
    def deserialize(cls, value):
        """
        Generates a Peer instance via a JSON string of the sort generated
        by `Peer.deserialize`.

        The `name` and `ip` keys are required to be present in the JSON map,
        if the `port` key is not present the default is used.
        """
        parsed = json.loads(value)

        if "name" not in parsed:
            raise ValueError("No peer name.")
        if "ip" not in parsed:
            raise ValueError("No peer IP.")
        if "port" not in parsed:
            parsed["port"] = DEFAULT_PEER_PORT

        return cls(parsed["name"], parsed["ip"], parsed["port"])

    def __hash__(self):
        """
        Hash method used to store peers in sets.

        Simply hashes the string <ip address>:<port>.
        """
        return hash(self.ip + ":" + str(self.port))

    def __eq__(self, other):
        """
        Peers are considered equal if their IP and port match.
        """
        return self.ip == other.ip and self.port == other.port
