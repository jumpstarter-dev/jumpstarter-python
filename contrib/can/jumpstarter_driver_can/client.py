from can import Message

from jumpstarter.client import DriverClient

from .common import CanMessage


class CanClient(DriverClient):
    def recv(self, timeout: float | None = None) -> None | Message:
        msg = CanMessage.model_validate(self.call("recv", timeout))
        if msg:
            return Message(**msg.__dict__)
        return None

    def send(self, msg: Message, timeout: float | None = None):
        self.call("send", CanMessage.model_validate(msg, from_attributes=True), timeout)
