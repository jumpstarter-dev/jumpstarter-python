from contextlib import suppress
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from anyio import TypedAttributeLookupError, TypedAttributeSet, typed_attribute
from anyio.abc import AnyByteStream, ObjectStream


class MetadataStreamAttributes(TypedAttributeSet):
    # https://grpc.io/docs/guides/metadata/
    metadata: dict[str, str] = typed_attribute()


@dataclass(kw_only=True)
class MetadataStream(ObjectStream[bytes]):
    stream: AnyByteStream
    metadata: dict[str, str]

    async def send(self, data: bytes) -> None:
        await self.stream.send(data)

    async def receive(self) -> bytes:
        return await self.stream.receive()

    async def send_eof(self) -> None:
        await self.stream.send_eof()

    async def aclose(self):
        await self.stream.aclose()

    @property
    def extra_attributes(self) -> Mapping[Any, Callable[[], Any]]:
        metadata = {}
        with suppress(TypedAttributeLookupError):
            metadata = self.stream.extra(MetadataStreamAttributes.metadata)
        return self.stream.extra_attributes | {MetadataStreamAttributes.metadata: lambda: metadata | self.metadata}
