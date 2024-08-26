import can
from can.interfaces.udp_multicast import UdpMulticastBus

from jumpstarter.common.utils import serve
from jumpstarter_driver_can.driver import Can


def test_client_can():
    with (
        serve(Can(channel=UdpMulticastBus.DEFAULT_GROUP_IPv6, interface="udp_multicast")) as client1,
        serve(Can(channel=UdpMulticastBus.DEFAULT_GROUP_IPv6, interface="udp_multicast")) as client2,
    ):
        msg = can.Message(data=b"hel\0lo")

        client1.send(msg)

        assert client2.recv().data == msg.data
