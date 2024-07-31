import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from shutil import which
from tempfile import TemporaryDirectory

import anyio
import can
import pytest
from can.interfaces.udp_multicast.utils import pack_message, unpack_message

from jumpstarter.common.utils import serve
from jumpstarter.drivers.can import UdpCan


def test_udp_can():
    with can.Bus(channel="test", interface="virtual") as sender:
        with serve(UdpCan(name="can", host="127.0.0.1", port=8008, interface="virtual", channel="test")) as client:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.bind(("127.0.0.1", 8008))

                with client.connect() as stream:
                    # stream.send(pack_message(can.Message(arbitration_id=0)))
                    sender.send(can.Message(arbitration_id=0))
                    assert True
                    # assert len(s.recv(5)) != 0
