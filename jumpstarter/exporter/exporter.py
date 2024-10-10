import logging
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from dataclasses import dataclass

from anyio import connect_unix, sleep
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
        with Session(
            uuid=self.uuid,
            labels=self.labels,
            root_device=self.device_factory(),
        ) as probe:
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

    @asynccontextmanager
    async def __handle(self, endpoint, token):
        root_device = self.device_factory()

        with Session(
            uuid=self.uuid,
            labels=self.labels,
            root_device=root_device,
        ) as session:
            async with session.serve_unix_async() as path:
                async with await connect_unix(path) as stream:
                    async with connect_router_stream(endpoint, token, stream):
                        yield

    async def serve(self):
        backoff = 5
        while True:
            logger.info("Listening for incoming events")
            try:
                response = await self.Listen(jumpstarter_pb2.ListenRequest())
            except Exception as e:
                logger.info("Listening for incoming events failed, retrying after %d seconds: %s", backoff, e)
                await sleep(backoff)
                continue
            logger.info("Handling new connection request")
            try:
                async with self.__handle(response.router_endpoint, response.router_token):
                    pass
            except Exception as e:
                logger.info("Error in handling connection: %s", e)
