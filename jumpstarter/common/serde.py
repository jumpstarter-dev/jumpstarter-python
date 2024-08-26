from google.protobuf import json_format, struct_pb2
from pydantic import TypeAdapter


def encode_value[T](v: T):
    adapter = TypeAdapter(T)
    return json_format.ParseDict(
        adapter.dump_python(v, mode="json"),
        struct_pb2.Value(),
    )


def decode_value[T](v: struct_pb2.Value) -> T:
    adapter = TypeAdapter(T)
    return adapter.validate_python(json_format.MessageToDict(v))
