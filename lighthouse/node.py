import json
import logging
import socket

from .peer import Peer


logger = logging.getLogger(__name__)


class Node(object):
    """
    The class representing a member node of a cluster.

    Consists of a `port`, a `host` and a `peer`, plus methods for serializing
    and deserializing themselves so that they can be transmitted back and
    forth via discovery methods.
    """

    def __init__(self, host, ip, port, peer=None, metadata=None):
        self.port = port
        self.host = host
        self.ip = ip
        self.peer = peer or Peer.current()
        self.metadata = metadata or {}

    @property
    def name(self):
        """
        Simple property for "naming" a node via the host and port.
        """
        return self.host + ":" + str(self.port)

    @classmethod
    def current(cls, service, port):
        """
        Returns a Node instance representing the current service node.

        Collects the host and IP information for the current machine and
        the port information from the given service.
        """
        host = socket.getfqdn()
        return cls(
            host=host,
            ip=socket.gethostbyname(host),
            port=port,
            metadata=service.metadata
        )

    def serialize(self):
        """
        Serializes the node data as a JSON map string.
        """
        return json.dumps({
            "port": self.port,
            "ip": self.ip,
            "host": self.host,
            "peer": self.peer.serialize() if self.peer else None,
            "metadata": json.dumps(self.metadata or {}, sort_keys=True),
        }, sort_keys=True)

    @classmethod
    def deserialize(cls, value):
        """
        Creates a new Node instance via a JSON map string.

        Note that `port` and `ip` and are required keys for the JSON map,
        `peer` and `host` are optional.  If `peer` is not present, the new Node
        instance will use the current peer.  If `host` is not present, the
        hostname of the given `ip` is looked up.
        """
        if getattr(value, "decode", None):
            value = value.decode()

        logger.debug("Deserializing node data: '%s'", value)
        parsed = json.loads(value)

        if "port" not in parsed:
            raise ValueError("No port defined for node.")
        if "ip" not in parsed:
            raise ValueError("No IP address defined for node.")
        if "host" not in parsed:
            host, aliases, ip_list = socket.gethostbyaddr(parsed["ip"])
            parsed["host"] = socket.get_fqdn(host)
        if "peer" in parsed:
            peer = Peer.deserialize(parsed["peer"])
        else:
            peer = None

        return cls(
            parsed["host"], parsed["ip"], parsed["port"],
            peer=peer, metadata=parsed.get("metadata")
        )

    def __eq__(self, other):
        """
        Nodes are considered equal if their IPs and ports both match.
        """
        return bool(self.ip == other.ip and self.port == other.port)
