import pytest

from jumpstarter.common.utils import serve
from jumpstarter.drivers.dutlink.base import Dutlink


def test_drivers_dutlink():
    try:
        instance = Dutlink(
            name="dutlink",
            storage_device="/dev/null",
        )
    except FileNotFoundError:
        pytest.skip("dutlink not available")

    with serve(instance) as client:
        with client.console.expect() as expect:
            expect.send("\x02" * 5)

            expect.send("about\r\n")
            expect.expect("Jumpstarter test-harness")

            expect.send("console\r\n")
            expect.expect("Entering console mode")

            client.power.off()

            client.storage.write_local_file("/dev/null")
            client.storage.dut()

            client.power.on()

            expect.send("\x02" * 5)
            expect.expect("Exiting console mode")

            client.power.off()
