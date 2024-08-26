from dataclasses import dataclass
from typing import List, Optional, Tuple

import can
from can.bus import _SelfRemovingCyclicTask

from jumpstarter.client import DriverClient

from .common import CanMessage, CanResult


@dataclass
class CanClient(DriverClient, can.BusABC):
    def __post_init__(self):
        self._periodic_tasks: List[_SelfRemovingCyclicTask] = []
        self.set_filters(None)
        self._is_shutdown: bool = False

        super().__post_init__()

    def _recv_internal(self, timeout: Optional[float]) -> Tuple[Optional[can.Message], bool]:
        result = CanResult.model_validate(self.call("_recv_internal", timeout))
        if result.msg:
            return can.Message(**CanMessage.model_validate(result.msg).__dict__), result.filtered
        return None, result.filtered

    def send(self, msg: can.Message, timeout: Optional[float] = None) -> None:
        self.call("send", CanMessage.model_validate(msg, from_attributes=True), timeout)

    def _apply_filters(self, filters: Optional[can.typechecking.CanFilters]) -> None:
        pass

    def flush_tx_buffer(self) -> None:
        self.call("flush_tx_buffer")
