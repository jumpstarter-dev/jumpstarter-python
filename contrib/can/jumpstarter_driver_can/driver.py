from dataclasses import InitVar, field
from typing import Optional

import can
from pydantic.dataclasses import dataclass

from jumpstarter.driver import Driver, export

from .common import CanMessage, CanResult


@dataclass(kw_only=True)
class Can(Driver):
    channel: InitVar[str | int | None]
    interface: InitVar[str | None]
    bus: can.Bus = field(init=False)

    @classmethod
    def client(cls) -> str:
        return "jumpstarter_driver_can.client.CanClient"

    def __post_init__(self, channel, interface):
        self.bus = can.Bus(channel=channel, interface=interface)

    @export
    def _recv_internal(self, timeout: Optional[float]) -> CanResult:
        msg, filtered = self.bus._recv_internal(timeout)
        if msg:
            return CanResult(msg=CanMessage.model_validate(msg, from_attributes=True), filtered=filtered)
        return CanResult(msg=None, filtered=filtered)

    @export
    def send(self, msg: CanMessage, timeout: float | None = None):
        self.bus.send(can.Message(**CanMessage.model_validate(msg).__dict__), timeout)

    @export
    def set_filters(self, filters: Optional[can.typechecking.CanFilters]) -> None:
        self.bus.set_filters(filters)

    @export
    def flush_tx_buffer(self) -> None:
        self.bus.flush_tx_buffer()
