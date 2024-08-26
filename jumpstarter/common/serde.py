from google.protobuf import json_format, struct_pb2
from pydantic import TypeAdapter


def encode_value[T](v: T):
    adapter = TypeAdapter(T)
    return json_format.ParseDict(
        adapter.dump_python(v, mode="json"),
        struct_pb2.Value(),
    )
