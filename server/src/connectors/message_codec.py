import msgpack

from errors import MalformedMessage


def decode_message(encoded_message: bytes) -> object:
    try:
        return msgpack.unpackb(encoded_message)
    except ValueError as decoding_error:
        raise MalformedMessage() from decoding_error


def encode_message(message_fields: dict) -> bytes:
    return msgpack.packb(message_fields)
