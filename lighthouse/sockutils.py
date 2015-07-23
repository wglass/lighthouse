import errno
import socket


def get_response(sock, buffer_size=4096):
    """
    Helper method for retrieving a response from a given socket.

    Returns two values in a tuple, the first is the reponse line and the second
    is any extra data after the newline.
    """
    response = ""
    extra = ""

    while True:
        try:
            chunk = sock.recv(buffer_size)
            if chunk:
                response += chunk
        except socket.error as e:
            if e.errno not in [errno.EAGAIN, errno.EINTR]:
                raise

        if not response:
            break

        if "\n" in response:
            response, extra = response.split("\n", 1)
            break

    return response, extra
