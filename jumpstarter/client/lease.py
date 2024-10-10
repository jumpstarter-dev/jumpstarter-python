import logging
from contextlib import AbstractAsyncContextManager, AbstractContextManager, asynccontextmanager, contextmanager
from dataclasses import dataclass, field

from anyio import fail_after, sleep
from anyio.from_thread import BlockingPortal
from google.protobuf import duration_pb2
from grpc.aio import Channel

from jumpstarter.client import client_from_path
from jumpstarter.common import MetadataFilter, TemporaryUnixListener
from jumpstarter.common.condition import condition_false, condition_true
from jumpstarter.common.streams import connect_router_stream
from jumpstarter.v1 import jumpstarter_pb2, jumpstarter_pb2_grpc, kubernetes_pb2

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class Lease(AbstractContextManager, AbstractAsyncContextManager):
    channel: Channel
    metadata_filter: MetadataFilter
    portal: BlockingPortal
    stub: jumpstarter_pb2_grpc.ControllerServiceStub = field(init=False)

    def __post_init__(self):
        self.stub = jumpstarter_pb2_grpc.ControllerServiceStub(self.channel)
        self.manager = self.portal.wrap_async_context_manager(self)

    async def __aenter__(self):
        duration = duration_pb2.Duration()
        duration.FromSeconds(1800)  # TODO: configurable duration

        logger.info("Leasing Exporter matching labels %s for %s", self.metadata_filter.labels, duration)
        self.lease = await self.stub.RequestLease(
            jumpstarter_pb2.RequestLeaseRequest(
                duration=duration,
                selector=kubernetes_pb2.LabelSelector(match_labels=self.metadata_filter.labels),
            )
        )
        logger.info("Lease %s created", self.lease.name)
        with fail_after(300):  # TODO: configurable timeout
            while True:
                logger.info("Polling Lease %s", self.lease.name)
                result = await self.stub.GetLease(jumpstarter_pb2.GetLeaseRequest(name=self.lease.name))

                # lease ready
                if condition_true(result.conditions, "Ready"):
                    logger.info("Lease %s acquired", self.lease.name)
                    return self
                # lease unsatisfiable
                if condition_true(result.conditions, "Unsatisfiable"):
                    raise ValueError("lease unsatisfiable")
                # lease not pending
                if condition_false(result.conditions, "Pending"):
                    raise ValueError("lease not pending")
                await sleep(1)

    async def __aexit__(self, exc_type, exc_value, traceback):
        logger.info("Releasing Lease %s", self.lease.name)
        await self.stub.ReleaseLease(jumpstarter_pb2.ReleaseLeaseRequest(name=self.lease.name))

    def __enter__(self):
        return self.manager.__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        return self.manager.__exit__(exc_type, exc_value, traceback)

    async def handle_async(self, stream):
        lease = await self.stub.GetLease(jumpstarter_pb2.GetLeaseRequest(name=self.lease.name))
        if not condition_true(lease.conditions, "Ready"):
            raise ValueError("lease not ready")

        logger.info("Connecting to Exporter with uuid %s", lease.exporter_uuid)

        response = await self.stub.Dial(jumpstarter_pb2.DialRequest(uuid=lease.exporter_uuid))
        async with connect_router_stream(response.router_endpoint, response.router_token, stream):
            pass

    @asynccontextmanager
    async def connect_async(self):
        async with TemporaryUnixListener(self.handle_async) as path:
            async with client_from_path(path, self.portal) as client:
                yield client

    @contextmanager
    def connect(self):
        with self.portal.wrap_async_context_manager(self.connect_async()) as client:
            yield client
