from threading import Semaphore

import can
from can.interfaces.udp_multicast import UdpMulticastBus

from jumpstarter.common.utils import serve
from jumpstarter_driver_can.driver import Can


def test_client_can():
    with (
        serve(Can(channel=UdpMulticastBus.DEFAULT_GROUP_IPv6, interface="udp_multicast")) as client1,
        serve(Can(channel=UdpMulticastBus.DEFAULT_GROUP_IPv6, interface="udp_multicast")) as client2,
    ):
        client1.send(can.Message(data=b"hello"))

        assert client2.recv().data == b"hello"


def test_client_can_filter():
    with (
        serve(Can(channel=UdpMulticastBus.DEFAULT_GROUP_IPv6, interface="udp_multicast")) as client1,
        serve(Can(channel=UdpMulticastBus.DEFAULT_GROUP_IPv6, interface="udp_multicast")) as client2,
    ):
        client2.set_filters([{"can_id": 0x1, "can_mask": 0x1, "extended": True}])

        client1.send(can.Message(arbitration_id=0x0, data=b"a"))
        client1.send(can.Message(arbitration_id=0x1, data=b"b"))
        client1.send(can.Message(arbitration_id=0x2, data=b"c"))

        assert client2.recv().data == b"b"


def test_client_can_notifier():
    with (
        serve(Can(channel=UdpMulticastBus.DEFAULT_GROUP_IPv6, interface="udp_multicast")) as client1,
        serve(Can(channel=UdpMulticastBus.DEFAULT_GROUP_IPv6, interface="udp_multicast")) as client2,
    ):
        sem = Semaphore(0)

        def listener(msg):
            assert msg.data == b"hello"
            sem.release()

        notifier = can.Notifier(client2, [listener])

        client1.send(can.Message(data=b"hello"))

        sem.acquire()
        notifier.stop()
