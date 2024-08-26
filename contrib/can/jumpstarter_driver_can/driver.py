from dataclasses import InitVar, field

from can import Bus, Message
from pydantic.dataclasses import dataclass

from jumpstarter.driver import Driver, export

from .common import CanMessage


@dataclass(kw_only=True)
class Can(Driver):
    channel: InitVar[str | int | None]
    interface: InitVar[str | None]
    bus: Bus = field(init=False)

    @classmethod
    def client(cls) -> str:
        return "jumpstarter_driver_can.client.CanClient"

    def __post_init__(self, channel, interface):
        self.bus = Bus(channel=channel, interface=interface)

    @export
    def recv(self, timeout: float | None = None) -> None | CanMessage:
        msg = self.bus.recv(timeout)
        if msg:
            return CanMessage.model_validate(msg, from_attributes=True)
        return None

    @export
    def send(self, msg: CanMessage, timeout: float | None = None):
        self.bus.send(Message(**CanMessage.model_validate(msg).__dict__), timeout)
