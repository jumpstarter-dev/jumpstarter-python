from dataclasses import dataclass

from jumpstarter.drivers import DriverClient
from jumpstarter.drivers.mixins import StreamMixin


@dataclass(kw_only=True)
class UdpCanClient(DriverClient, StreamMixin):
    pass
