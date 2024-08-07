from concurrent.futures import ThreadPoolExecutor

from gpiozero import Device
from gpiozero.pins.mock import MockFactory
from jumpstarter_driver_raspberrypi.gpio.digital import DigitalInput, DigitalOutput

from jumpstarter.common.utils import serve

Device.pin_factory = MockFactory()


def test_drivers_gpio_digital_output():
    instance = DigitalOutput(name="digital_output", pin=1)

    with serve(instance) as client:
        client.off()
        client.on()
        client.off()

    instance.device.pin.assert_states((False, True, False))


def test_drivers_gpio_digital_input():
    instance = DigitalInput(name="digital_input", pin=4)

    with serve(instance) as client:
        with ThreadPoolExecutor() as pool:
            pool.submit(client.wait_for_active)
            instance.device.pin.drive_high()

        with ThreadPoolExecutor() as pool:
            pool.submit(client.wait_for_inactive)
            instance.device.pin.drive_low()
