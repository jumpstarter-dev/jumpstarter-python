import os
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

import grpc
from anyio.from_thread import start_blocking_portal

from jumpstarter.client import LeaseRequest, client_from_channel
from jumpstarter.common.grpc import insecure_channel
from jumpstarter.exporter import Session


async def _create_grpc_server():
    return grpc.aio.server()


@contextmanager
def serve(root_device):
    with start_blocking_portal() as portal:
        server = portal.call(_create_grpc_server)

        session = Session(name="session", root_device=root_device)
        session.add_to_server(server)

        with TemporaryDirectory() as tempdir:
            socketpath = Path(tempdir) / "socket"
            server.add_insecure_port(f"unix://{socketpath}")

            portal.call(server.start)

            with portal.wrap_async_context_manager(portal.call(insecure_channel, f"unix://{socketpath}")) as channel:
                yield portal.call(client_from_channel, channel, portal)

            portal.call(server.stop, None)


@contextmanager
def environment():
    host = os.environ.get("JUMPSTARTER_HOST")
    with start_blocking_portal() as portal:
        channel = portal.call(insecure_channel, host)
        client = portal.call(client_from_channel, channel, portal)
        yield client


@contextmanager
def lease(metadata_filter):
    with start_blocking_portal() as portal:
        with LeaseRequest(
            channel=portal.call(insecure_channel, "localhost:8083"),
            metadata_filter=metadata_filter,
            portal=portal,
        ) as lease:
            with lease.connect() as client:
                yield client
