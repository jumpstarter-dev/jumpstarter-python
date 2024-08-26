from dataclasses import dataclass
from typing import List, Optional, Tuple

import can
from can.bus import _SelfRemovingCyclicTask
from pydantic import ConfigDict, validate_call

from jumpstarter.client import DriverClient

from .common import CanMessage, CanResult


@dataclass
class CanClient(DriverClient, can.BusABC):
    def __post_init__(self):
        self._periodic_tasks: List[_SelfRemovingCyclicTask] = []
        self._filters = None
        self._is_shutdown: bool = False

        super().__post_init__()

    @validate_call(validate_return=True, config=ConfigDict(arbitrary_types_allowed=True))
    def _recv_internal(self, timeout: Optional[float]) -> Tuple[Optional[can.Message], bool]:
        result = CanResult.model_validate(self.call("_recv_internal", timeout))
        if result.msg:
            return can.Message(**CanMessage.model_validate(result.msg).__dict__), result.filtered
        return None, result.filtered

    @validate_call(validate_return=True, config=ConfigDict(arbitrary_types_allowed=True))
    def send(self, msg: can.Message, timeout: Optional[float] = None) -> None:
        self.call("send", CanMessage.model_validate(msg, from_attributes=True), timeout)

    @validate_call(validate_return=True)
    def _apply_filters(self, filters: Optional[can.typechecking.CanFilters]) -> None:
        self.call("_apply_filters", filters)

    @validate_call(validate_return=True)
    def flush_tx_buffer(self) -> None:
        self.call("flush_tx_buffer")
