import re
from typing import Any, Optional, TypeAlias
from .dtypes import ArrayLike
import numpy

__all__ = [
    "Device",
    "DeviceLike",
    "get_available_devices",
    "get_array_device",
    "set_random_seed",
    "array_to_string",
    "select_device",
    "parse_device",
    "move_to_device",
    "set_nn_device",
    "get_nn_device",
]

_MAX_LINE_WIDTH = 200
_PRECISION = 4
_FLOAT_MODE = "maxprec_equal"

_CPU_BACKEND = numpy
_CPU_BACKEND.set_printoptions(precision=_PRECISION, linewidth=_MAX_LINE_WIDTH, floatmode=_FLOAT_MODE)

try:
    import cupy

    _CUDA_BACKEND = cupy
    _CUDA_BACKEND.set_printoptions(precision=_PRECISION, linewidth=_MAX_LINE_WIDTH, floatmode=_FLOAT_MODE)
except ImportError:
    _CUDA_BACKEND = None


def cuda_available():
    return _CUDA_BACKEND is not None and _CUDA_BACKEND.cuda.is_available()


def set_random_seed(seed: int):
    _CPU_BACKEND.random.seed(seed)
    if cuda_available():
        _CUDA_BACKEND.random.seed(seed)


def array_to_string(data: ArrayLike, prefix: str) -> str:
    device = get_array_device(data)
    return device.xp.array2string(
        data,
        max_line_width=_MAX_LINE_WIDTH,
        precision=_PRECISION,
        separator=", ",
        prefix=prefix,
        floatmode=_FLOAT_MODE,
    )


def _get_type_and_id(device_type: str) -> tuple[str, Optional[int]]:
    match = re.match(r"(?P<type>cpu|cuda)(?::(?P<id>\d+))?", device_type)
    if match:
        device_type = match.group("type")
        if device_type == "cuda":
            assert cuda_available(), "CUDA is not available."
        device_id = match.group("id")
        return device_type, None if device_id is None else int(device_id)
    raise ValueError(f"Unknown device: {device_type}")


class Device:
    def __init__(self, dev_type: str):
        dev_type, dev_id = _get_type_and_id(dev_type)
        self.dev_type = dev_type
        self.dev_id = dev_id
        self.xp = _CPU_BACKEND if dev_type == "cpu" else _CUDA_BACKEND

    def __eq__(self, other: Any) -> bool:
        return (
                isinstance(other, Device)
                and other.dev_type == self.dev_type
                and other.dev_id == self.dev_id
        )

    def __repr__(self) -> str:
        id_suffix = f":{self.dev_id}" if self.dev_type == "cuda" else ""
        return f"device('{self.dev_type}{id_suffix}')"

    def __str__(self) -> str:
        id_suffix = f":{self.dev_id}" if self.dev_type == "cuda" else ""
        return f"{self.dev_type}{id_suffix}"

    def __enter__(self) -> None:
        if self.dev_type == "cpu":
            return None
        return _CUDA_BACKEND.cuda.Device(self.dev_id).__enter__()

    def __exit__(self, *args: Any) -> None:
        if self.dev_type == "cpu":
            return None
        return _CUDA_BACKEND.cuda.Device(self.dev_id).__exit__(*args)


DeviceLike: TypeAlias = Device | str


def get_available_devices() -> list[str]:
    devices = ["cpu"]
    if _CUDA_BACKEND is not None:
        num_cuda_devices = _CUDA_BACKEND.cuda.runtime.getDeviceCount()
        cuda_devices = [f"cuda:{i}" for i in range(num_cuda_devices)]
        devices.extend(cuda_devices)
    return devices


def get_array_device(x: ArrayLike) -> Device:
    return Device("cpu") if "numpy" in str(type(x)) else Device("cuda:0")


def select_device(device: Optional[DeviceLike]) -> Device:
    if isinstance(device, Device):
        return device
    return Device(device or "cpu")


def parse_device(device: DeviceLike) -> Device:
    return device if isinstance(device, Device) else Device(device)


def move_to_device(data: ArrayLike, device: Device) -> ArrayLike:
    if device == Device("cpu"):
        return _CUDA_BACKEND.asnumpy(data)
    assert cuda_available(), "CUDA is not available."
    return cupy.asarray(data)


_NN_DEVICE = Device("cpu")


def set_nn_device(device: str) -> None:
    global _NN_DEVICE
    devices = get_available_devices()
    if device in devices:
        _NN_DEVICE = Device(device)
    else:
        _NN_DEVICE = Device("cpu")
        print(f">>> {device} is not available, Using CPU as default ...")


def get_nn_device() -> Device:
    return _NN_DEVICE
