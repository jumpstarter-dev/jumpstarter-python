import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Optional

import can
from anyio import create_connected_udp_socket, create_task_group
from can.interfaces.udp_multicast.utils import pack_message, unpack_message
from can.typechecking import Channel

from jumpstarter.drivers import exportstream
from jumpstarter.drivers.network import UdpNetwork


@dataclass(kw_only=True)
class UdpCan(UdpNetwork):
    """A CAN over UDP multicast driver."""

    # CAN configuration for local channel only
    channel: Optional[Channel] = None
    interface: Optional[str] = None
    config_context: Optional[str] = None
    ignore_config: bool = False
    fd: bool = False

    @classmethod
    def client(cls) -> str:
        return "jumpstarter.drivers.can.client.UdpCanClient"

    @exportstream
    @asynccontextmanager
    async def connect(self):
        async with create_task_group() as tg:
            async with await create_connected_udp_socket(remote_host=self.host, remote_port=self.port) as stream:
                with can.Bus(
                    channel=self.channel,
                    interface=self.interface,
                    config_context=self.config_context,
                    ignore_config=self.ignore_config,
                ) as bus:
                    async def send_msg():
                        print("Started send task!")
                        async for data in stream:
                            print("Got remote message!")
                            msg = unpack_message(data, check=True)
                            bus.send(msg)

                    async def recv_msg():
                        print("Started receive task!")
                        async for msg in bus:
                            print("Got message locally!")
                            if self.fd and msg.is_fd:
                                raise can.CanOperationError("cannot send FD message over bus with CAN FD disabled")
                            data = pack_message(msg)
                            stream.send(data)

                    tg.start_soon(send_msg)
                    tg.start_soon(recv_msg)

                    yield stream

                    # notifier.stop()
                    # tg.cancel_scope.cancel()
