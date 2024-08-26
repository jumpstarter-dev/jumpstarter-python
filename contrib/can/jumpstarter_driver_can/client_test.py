import can
from can.interfaces.udp_multicast import UdpMulticastBus

from jumpstarter.common.utils import serve
from jumpstarter_driver_can.driver import Can


def test_client_can():
    with (
        serve(Can(channel=UdpMulticastBus.DEFAULT_GROUP_IPv6, interface="udp_multicast")) as client1,
        serve(Can(channel=UdpMulticastBus.DEFAULT_GROUP_IPv6, interface="udp_multicast")) as client2,
    ):
        msg = can.Message(data=b"hello")

        client1.send(msg)

        assert client2.recv().data == msg.data

        client2.set_filters([{"can_id": 0x1, "can_mask": 0x1, "extended": True}])

        client1.send(can.Message(arbitration_id=0x0, data=b"a"))
        client1.send(can.Message(arbitration_id=0x1, data=b"b"))
        client1.send(can.Message(arbitration_id=0x2, data=b"c"))

        assert client2.recv().data == b"b"
