from typing import Optional

from pydantic import BaseModel


class CanMessage(BaseModel):
    timestamp: float
    arbitration_id: int
    is_extended_id: bool
    is_remote_frame: bool
    is_error_frame: bool
    channel: Optional[int | str]
    dlc: Optional[int]
    data: Optional[bytes]
    is_fd: bool
    is_rx: bool
    bitrate_switch: bool
    error_state_indicator: bool
