import collections
import errno
import logging
import os
import re
import socket
import subprocess

from lighthouse.peer import Peer


SOCKET_BUFFER_SIZE = 8192

version_re = re.compile('.*(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+).*')
first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')


logger = logging.getLogger(__name__)


class HAProxyControl(object):
    """
    Class used to control a running HAProxy process.

    Includes basic functionality for soft restarts as well as gathering info
    about the HAProxy process and its active nodes, plus methods for enabling
    or disabling nodes on the fly.

    Also allows for sending commands to the HAProxy control socket itself.
    """

    def __init__(self, config_file_path, socket_file_path, pid_file_path):
        self.config_file_path = config_file_path
        self.socket_file_path = socket_file_path
        self.pid_file_path = pid_file_path

        self.peer = Peer.current()

    def restart(self):
        """
        Performs a soft reload of the HAProxy process.
        """
        version = self.get_version()

        command = [
            "haproxy",
            "-f", self.config_file_path, "-p", self.pid_file_path
        ]
        if version and version >= (1, 5, 0):
            command.extend(["-L", self.peer.name])
        if os.path.exists(self.pid_file_path):
            with open(self.pid_file_path) as fd:
                command.extend(["-sf", fd.read().replace("\n", "")])

        try:
            output = subprocess.check_output(command)
        except subprocess.CalledProcessError as e:
            logger.error("Failed to restart HAProxy: %s", str(e))
            return

        if output:
            logging.error("haproxy says: %s", output)

        logger.info("Gracefully restarted HAProxy.")

    def get_version(self):
        """
        Returns a tuple representing the installed HAProxy version.

        The value of the tuple is (<major>, <minor>, <patch>), e.g. if HAProxy
        version 1.5.3 is installed, this will return `(1, 5, 3)`.
        """
        command = ["haproxy", "-v"]
        try:
            output = subprocess.check_output(command)
            version_line = output.split("\n")[0]
        except subprocess.CalledProcessError as e:
            logger.error("Could not get HAProxy version: %s", str(e))
            return None

        match = version_re.match(version_line)
        if not match:
            logger.error("Could not parse version from '%s'", version_line)
            return None

        version = (
            int(match.group("major")),
            int(match.group("minor")),
            int(match.group("patch"))
        )

        logger.debug("Got HAProxy version: %s", version)

        return version

    def get_info(self):
        """
        Parses the output of a "show info" HAProxy command and returns a
        simple dictionary of the results.
        """
        info_response = self.send_command("show info")

        if not info_response:
            return {}

        def convert_camel_case(string):
            return all_cap_re.sub(
                r'\1_\2',
                first_cap_re.sub(r'\1_\2', string)
            ).lower()

        return dict(
            (convert_camel_case(label), value)
            for label, value in [
                line.split(": ")
                for line in info_response.split("\n")
            ]
        )

    def get_active_nodes(self):
        """
        Returns a dictionary of lists, where the key is the name of a service
        and the list includes all active nodes associated with that service.
        """
        # the -1 4 -1 args are the filters <proxy_id> <type> <server_id>,
        # -1 for all proxies, 4 for servers only, -1 for all servers
        stats_response = self.send_command("show stat -1 4 -1")
        if not stats_response:
            return []

        lines = stats_response.split("\n")
        fields = lines.pop(0).split(",")
        # the first field is the service name, which we key off of so
        # it's not included in individual node records
        fields.pop(0)

        active_nodes = collections.defaultdict(list)

        for line in lines:
            values = line.split(",")
            service_name = values.pop(0)
            active_nodes[service_name].append(
                dict(
                    (fields[i], values[i])
                    for i in range(len(fields))
                )
            )

        return active_nodes

    def enable_node(self, service_name, node_name):
        """
        Enables a given node name for the given service name via the
        "enable server" HAProxy command.
        """
        logger.info("Enabling server %s/%s", service_name, node_name)
        return self.send_command(
            "enable server %s/%s" % (service_name, node_name)
        )

    def disable_node(self, service_name, node_name):
        """
        Disables a given node name for the given service name via the
        "disable server" HAProxy command.
        """
        logger.info("Disabling server %s/%s", service_name, node_name)
        return self.send_command(
            "disable server %s/%s" % (service_name, node_name)
        )

    def send_command(self, command):
        """
        Sends a given command to the HAProxy control socket.

        Returns the response from the socket as a string.

        If a known error response (e.g. "Permission denied.") is given then
        the appropriate exception is raised.
        """
        logger.debug("Connecting to socket %s", self.socket_file_path)
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(self.socket_file_path)
        except IOError as e:
            if e.errno == errno.ECONNREFUSED:
                logger.error("Connection refused.  Is HAProxy running?")
                return
            else:
                raise

        sock.sendall((command + "\n").encode())

        response = b""
        while True:
            try:
                chunk = sock.recv(SOCKET_BUFFER_SIZE)
                if chunk:
                    response += chunk
                else:
                    break
            except IOError as e:
                if e.errno not in (errno.EAGAIN, errno.EINTR):
                    raise

        sock.close()

        return self.process_command_response(command, response)

    def process_command_response(self, command, response):
        """
        Takes an HAProxy socket command and its response and either raises
        an appropriate exception or returns the formatted response.
        """
        if response.startswith(b"Unknown command."):
            raise UnknownCommandError(command)
        if response == b"Permission denied.\n":
            raise PermissionError(command)
        if response == b"No such backend.\n":
            raise UnknownServerError(command)

        response = response.decode()
        return response.rstrip("\n")


class HAProxyControlError(Exception):
    """
    Base exception for HAProxyControl-related actions.
    """
    pass


class UnknownCommandError(HAProxyControlError):
    """
    Exception raised if an unrecognized command was sent to the HAProxy socket.
    """
    pass


class PermissionError(HAProxyControlError):
    """
    Exception denoting that the HAProxy control socket does not have proper
    authentication level for executing a given command.

    For example, if the socket is set up with a a level lower than "admin",
    the enable/disable server commands will fail.
    """
    pass


class UnknownServerError(HAProxyControlError):
    """
    Exception raised if an enable/disable server command is executed against
    a backend that HAProxy doesn't know about.
    """
    pass
