import zmq

from constants import CLIENT_FACING_ENDPOINT, SERVER_FACING_ENDPOINT


def bound_socket(context: zmq.Context, socket_type: int, endpoint: str) -> zmq.Socket:
    socket = context.socket(socket_type)
    socket.bind(endpoint)
    return socket


def main() -> None:
    context = zmq.Context()
    client_facing_socket = bound_socket(context, zmq.ROUTER, CLIENT_FACING_ENDPOINT)
    server_facing_socket = bound_socket(context, zmq.DEALER, SERVER_FACING_ENDPOINT)
    print(f"BROKER | clients on {CLIENT_FACING_ENDPOINT} | servers on {SERVER_FACING_ENDPOINT}", flush=True)
    zmq.proxy(client_facing_socket, server_facing_socket)


if __name__ == "__main__":
    main()
