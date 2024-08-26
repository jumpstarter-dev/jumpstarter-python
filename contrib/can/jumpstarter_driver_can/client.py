from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence, Tuple, Union
from uuid import UUID

import can
from can.bus import _SelfRemovingCyclicTask
from pydantic import ConfigDict, validate_call

from jumpstarter.client import DriverClient

from .common import CanMessage, CanResult


@dataclass(kw_only=True)
class RemoteCyclicSendTask(can.broadcastmanager.CyclicSendTaskABC):
    client: CanClient
    uuid: UUID

    def stop(self) -> None:
        self.client.call("_stop_task", self.uuid)


@dataclass(kw_only=True)
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

    @validate_call(validate_return=True, config=ConfigDict(arbitrary_types_allowed=True))
    def _send_periodic_internal(
        self,
        msgs: Union[Sequence[can.Message], can.Message],
        period: float,
        duration: Optional[float] = None,
        modifier_callback: Optional[Callable[[can.Message], None]] = None,
    ) -> can.broadcastmanager.CyclicSendTaskABC:
        if modifier_callback:
            return super()._send_periodic_internal(msgs, period, duration, modifier_callback)
        else:
            if isinstance(msgs, can.Message):
                msgs = [CanMessage.model_validate(msgs, from_attributes=True)]
            elif isinstance(msgs, Sequence):
                msgs = [CanMessage.model_validate(msg, from_attributes=True) for msg in msgs]
            return RemoteCyclicSendTask(client=self, uuid=self.call("_send_periodic_internal", msgs, period, duration))

    @validate_call(validate_return=True)
    def _apply_filters(self, filters: Optional[can.typechecking.CanFilters]) -> None:
        self.call("_apply_filters", filters)

    @validate_call(validate_return=True)
    def flush_tx_buffer(self) -> None:
        self.call("flush_tx_buffer")

    @validate_call(validate_return=True)
    def shutdown(self) -> None:
        self.call("shutdown")
        super().shutdown()
