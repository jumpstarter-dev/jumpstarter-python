from dataclasses import InitVar, field
from typing import Callable, Optional, Sequence, Union
from uuid import UUID, uuid4

import can
from pydantic import ConfigDict, validate_call
from pydantic.dataclasses import dataclass

from jumpstarter.driver import Driver, export

from .common import CanMessage, CanResult


@dataclass(kw_only=True, config=ConfigDict(arbitrary_types_allowed=True))
class Can(Driver):
    channel: InitVar[str | int | None]
    interface: InitVar[str | None]
    bus: can.Bus = field(init=False)

    __tasks: dict[UUID, can.broadcastmanager.CyclicSendTaskABC] = field(init=False, default_factory=dict)

    @classmethod
    def client(cls) -> str:
        return "jumpstarter_driver_can.client.CanClient"

    def __post_init__(self, channel, interface):
        self.bus = can.Bus(channel=channel, interface=interface)

    @export
    @validate_call(validate_return=True)
    def _recv_internal(self, timeout: Optional[float]) -> CanResult:
        msg, filtered = self.bus._recv_internal(timeout)
        if msg:
            return CanResult(msg=CanMessage.model_validate(msg, from_attributes=True), filtered=filtered)
        return CanResult(msg=None, filtered=filtered)

    @export
    @validate_call(validate_return=True)
    def send(self, msg: CanMessage, timeout: float | None = None):
        self.bus.send(can.Message(**msg.__dict__), timeout)

    @export
    @validate_call(validate_return=True, config=ConfigDict(arbitrary_types_allowed=True))
    def _send_periodic_internal(
        self,
        msgs: Union[Sequence[CanMessage], CanMessage],
        period: float,
        duration: Optional[float] = None,
        modifier_callback: Optional[Callable[[can.Message], None]] = None,
    ) -> UUID:
        assert modifier_callback is None
        task = self.bus._send_periodic_internal(msgs, period, duration, modifier_callback)
        uuid = uuid4()
        self.__tasks[uuid] = task
        return uuid

    @export
    @validate_call(validate_return=True)
    def _stop_task(self, uuid: UUID):
        self.__tasks.pop(uuid).stop()

    @export
    @validate_call(validate_return=True)
    def _apply_filters(self, filters: Optional[can.typechecking.CanFilters]) -> None:
        self.bus._apply_filters(filters)

    @export
    @validate_call(validate_return=True)
    def flush_tx_buffer(self) -> None:
        self.bus.flush_tx_buffer()

    @export
    @validate_call(validate_return=True)
    def shutdown(self) -> None:
        self.bus.shutdown()
