import zmq

from constants import PUBLISHER_FACING_ENDPOINT, SUBSCRIBER_FACING_ENDPOINT


def bound_socket(context: zmq.Context, socket_type: int, endpoint: str) -> zmq.Socket:
    socket = context.socket(socket_type)
    socket.bind(endpoint)
    return socket


def main() -> None:
    context = zmq.Context()
    publisher_facing_socket = bound_socket(context, zmq.XSUB, PUBLISHER_FACING_ENDPOINT)
    subscriber_facing_socket = bound_socket(context, zmq.XPUB, SUBSCRIBER_FACING_ENDPOINT)
    print(f"PROXY | publishers on {PUBLISHER_FACING_ENDPOINT} | subscribers on {SUBSCRIBER_FACING_ENDPOINT}", flush=True)
    zmq.proxy(publisher_facing_socket, subscriber_facing_socket)


if __name__ == "__main__":
    main()
