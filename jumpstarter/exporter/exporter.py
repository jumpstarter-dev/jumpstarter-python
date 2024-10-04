import logging
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass

from anyio import connect_unix, create_task_group, sleep
from grpc.aio import Channel

from jumpstarter.common import Metadata
from jumpstarter.common.streams import connect_router_stream
from jumpstarter.driver import Driver
from jumpstarter.exporter.session import Session
from jumpstarter.v1 import (
    jumpstarter_pb2,
    jumpstarter_pb2_grpc,
)

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class Exporter(AbstractAsyncContextManager, Metadata):
    channel: Channel
    device_factory: Callable[[], Driver]

    def __post_init__(self):
        super().__post_init__()
        jumpstarter_pb2_grpc.ControllerServiceStub.__init__(self, self.channel)

    async def __aenter__(self):
        probe = Session(
            uuid=self.uuid,
            labels=self.labels,
            root_device=self.device_factory(),
        )

        logger.info("Registering exporter with controller")
        await self.Register(
            jumpstarter_pb2.RegisterRequest(
                labels=self.labels,
                reports=(await probe.GetReport(None, None)).reports,
            )
        )

        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        logger.info("Unregistering exporter with controller")
        await self.Unregister(
            jumpstarter_pb2.UnregisterRequest(
                reason="TODO",
            )
        )

    async def __handle(self, endpoint, token):
        root_device = self.device_factory()

        session = Session(
            uuid=self.uuid,
            labels=self.labels,
            root_device=root_device,
        )

        async with session.serve_unix_async() as path:
            async with await connect_unix(path) as stream:
                async with connect_router_stream(endpoint, token, stream):
                    pass

    async def serve(self):
        logger.info("Listening for incoming connection requests")
        async with create_task_group() as tg:
            async for request in self.Listen(jumpstarter_pb2.ListenRequest()):
                logger.info("Handling new connection request")
                tg.start_soon(self.__handle, request.router_endpoint, request.router_token)

    async def serve_forever(self):
        backoff = 5
        while True:
            try:
                await self.serve()
            except Exception as e:
                logger.info("Exporter: connection interrupted, reconnecting after %d seconds: %s", backoff, e)
                await sleep(backoff)
