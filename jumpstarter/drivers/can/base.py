import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Optional

import anyio
import can
from anyio import create_connected_udp_socket
from can.interfaces.udp_multicast import UdpMulticastBus
from can.typechecking import Channel

from jumpstarter.drivers import exportstream
from jumpstarter.drivers.network import UdpNetwork


async def pipe_can(source: can.BusABC, dest: can.BusABC):
    """Pipe CAN messages from a source bus to a dest bus."""
    try:
        while True:
            # Read a message from the source CAN bus
            message = await asyncio.get_event_loop().run_in_executor(None, source.recv)
            if message is not None:
                print(f"Received message: {message}")
                # Send the message to the destination CAN bus
                await asyncio.get_event_loop().run_in_executor(None, dest.send, message)
                print(f"Sent message: {message}")
    except Exception as e:
        print(f"Error in CAN piping: {e}")


@dataclass(kw_only=True)
class UdpCan(UdpNetwork):
    """A CAN over UDP multicast driver."""

    # CAN configuration for local channel only
    channel: Optional[Channel] = None
    interface: Optional[str] = None
    config_context: Optional[str] = None
    ignore_config: bool = False
    fd: bool = False

    source: can.BusABC = field(init=False)
    """The local source CAN bus."""

    @classmethod
    def client(cls) -> str:
        return "jumpstarter.drivers.can.client.UdpCanClient"

    def __post_init__(self, *args):
        # Setup source CAN channel with any interface allowed
        self.source = can.Bus(
            channel=self.channel,
            interface=self.interface,
            config_context=self.config_context,
            ignore_config=self.ignore_config,
        )

    @exportstream
    @asynccontextmanager
    async def connect(self):
        try:
            # Setup broadcast channel with UDP multicast bus
            bus = UdpMulticastBus(channel=self.host, port=self.port, fd=self.fd)

            # Wrap the raw socket in an anyio-compatible way
            # async with anyio.create_connected_udp_socket(bus._multicast._socket) as stream:
        finally:
            bus.shutdown()
        # async with await create_connected_udp_socket(remote_host=self.host, remote_port=self.port) as stream:
        #     yield stream

    # @exportstream
    # @asynccontextmanager
    # async def connect(self):
    #     async with await create_connected_udp_socket(remote_host=self.host, remote_port=self.port) as stream:
    #         # Start a background task to pipe CAN messages
    #         pipe_task = asyncio.create_task(pipe_can(self.source, self.broadcast))
    #         try:
    #             # Yield the UDP stream
    #             yield stream
    #         finally:
    #             # Cancel the pipe task when exiting the context
    #             pipe_task.cancel()
    #             await pipe_task  # Wait for the pipe task to finish

    # def shutdown(self):
    #     """Shut down the CAN buses."""
    #     if self.source is not None:
    #         self.source.shutdown()
    #     if self.broadcast is not None:
    #         self.broadcast.shutdown()

    # def __del__(self):
    #     self.shutdown()
