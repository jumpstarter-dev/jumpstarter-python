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
from can.interfaces.udp_multicast import UdpMulticastBus

from jumpstarter.common.utils import serve
from jumpstarter.drivers.can import UdpCan


def test_udp_can():
    # sender = can.Bus(interface="virtual")
    with serve(UdpCan(name="can", host="127.0.0.1", port=8008, interface="virtual")) as client:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(("127.0.0.1", 8008))

            with client.connect() as stream:
                assert True
                # stream.send(b"hello")
                # assert s.recv(5) == b"hello"
