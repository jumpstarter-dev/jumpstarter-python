from itertools import islice
from threading import Semaphore

import can

from jumpstarter.common.utils import serve
from jumpstarter_driver_can.driver import Can


def test_client_can(request):
    with (
        serve(Can(channel=request.node.name, interface="virtual")) as client1,
        serve(Can(channel=request.node.name, interface="virtual")) as client2,
    ):
        client1.send(can.Message(data=b"hello"))

        assert client2.recv().data == b"hello"

        del client1, client2


def test_client_can_iterator(request):
    with (
        serve(Can(channel=request.node.name, interface="virtual")) as client1,
        serve(Can(channel=request.node.name, interface="virtual")) as client2,
    ):
        client1.send(can.Message(data=b"a"))
        client1.send(can.Message(data=b"b"))
        client1.send(can.Message(data=b"c"))

        assert [msg.data for msg in islice(client2, 3)] == [b"a", b"b", b"c"]

        del client1, client2


def test_client_can_filter(request):
    with (
        serve(Can(channel=request.node.name, interface="virtual")) as client1,
        serve(Can(channel=request.node.name, interface="virtual")) as client2,
    ):
        client2.set_filters([{"can_id": 0x1, "can_mask": 0x1, "extended": True}])

        client1.send(can.Message(arbitration_id=0x0, data=b"a"))
        client1.send(can.Message(arbitration_id=0x1, data=b"b"))
        client1.send(can.Message(arbitration_id=0x2, data=b"c"))

        assert client2.recv().data == b"b"

        del client1, client2


def test_client_can_notifier(request):
    with (
        serve(Can(channel=request.node.name, interface="virtual")) as client1,
        serve(Can(channel=request.node.name, interface="virtual")) as client2,
    ):
        sem = Semaphore(0)

        def listener(msg):
            assert msg.data == b"hello"
            sem.release()

        notifier = can.Notifier(client2, [listener])

        client1.send(can.Message(data=b"hello"))

        sem.acquire()
        notifier.stop()

        del client1, client2, notifier


def test_client_can_redirect(request):
    with (
        serve(Can(channel=request.node.name, interface="virtual")) as client1,
        serve(Can(channel=request.node.name, interface="virtual")) as client2,
    ):
        bus3 = can.interface.Bus(request.node.name + "_inner", interface="virtual")
        bus4 = can.interface.Bus(request.node.name + "_inner", interface="virtual")

        notifier = can.Notifier(client2, [can.RedirectReader(bus3)])

        client1.send(can.Message(data=b"hello"))

        assert bus4.recv().data == b"hello"

        notifier.stop()

        del client1, client2, notifier
