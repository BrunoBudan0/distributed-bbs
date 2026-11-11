from uuid import uuid4


def new_username() -> str:
    return f"user-{uuid4().hex[:16]}"


def new_channel_name() -> str:
    return f"channel-{uuid4().hex[:16]}"


def new_server_name() -> str:
    return f"server-{uuid4().hex[:16]}"
