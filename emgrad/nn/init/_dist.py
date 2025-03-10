from functools import reduce
from typing import Literal
from emgrad.autograd import Tensor
from emgrad._backends import get_nn_device
import emgrad.autograd as ad

FanMode = Literal["fan_in", "fan_out"]

__all__ = [
    "uniform",
    "normal",
    "constant",
    "xavier_uniform",
    "xavier_normal",
    "kaiming_uniform",
    "kaiming_normal",
]


def _calculate_fan_in_and_fan_out(*shape: int) -> tuple[int, int]:
    if len(shape) == 2:
        fan_in = shape[0]
        fan_out = shape[1]

    elif len(shape) in [3, 4, 5]:
        kernel_prod = reduce(lambda x, y: x * y, shape[2:], 1)
        fan_in = shape[1] * kernel_prod
        fan_out = shape[0] * kernel_prod

    else:
        raise ValueError(
            f"Tensor with dims {shape} is not supported. Must be at least 2D."
        )

    return fan_in, fan_out


def uniform(*shape: int, low: float = -1, high: float = 1, req_grad: bool = False) -> Tensor:
    return ad.random.uniform(*shape, low=low, high=high, device=get_nn_device(), req_grad=req_grad)


def normal(*shape: int, mean: float = 0, std: float = 1, req_grad: bool = False) -> Tensor:
    return ad.random.randn(*shape, mean=mean, std=std, device=get_nn_device(), req_grad=req_grad)


def constant(*shape: int, value: float = 1.0, req_grad: bool = False) -> Tensor:
    return ad.full(*shape, value=value, device=get_nn_device(), req_grad=req_grad)


def xavier_uniform(*shape: int, gain: float = 1.0, req_grad: bool = False) -> Tensor:
    fan_in, fan_out = _calculate_fan_in_and_fan_out(*shape)
    bound = (6 / (fan_in + fan_out)) ** 0.5 * gain
    return ad.random.uniform(*shape, low=-bound, high=bound, device=get_nn_device(), req_grad=req_grad)


def xavier_normal(*shape: int, gain: float = 1.0, req_grad: bool = False) -> Tensor:
    fan_in, fan_out = _calculate_fan_in_and_fan_out(*shape)
    std = (2 / (fan_in + fan_out)) ** 0.5 * gain
    return ad.random.randn(*shape, mean=0, std=std, device=get_nn_device(), req_grad=req_grad)


def kaiming_uniform(*shape: int, mode: FanMode = "fan_in", req_grad: bool = False) -> Tensor:
    if mode not in {"fan_in", "fan_out"}:
        raise ValueError("mode must be either 'fan_in' or 'fan_out'.")
    fan_in, fan_out = _calculate_fan_in_and_fan_out(*shape)
    fan = fan_in if mode == "fan_in" else fan_out
    bound = (6 / fan) ** 0.5
    return ad.random.uniform(*shape, low=-bound, high=bound, device=get_nn_device(), req_grad=req_grad)


def kaiming_normal(*shape: int, mode: FanMode = "fan_in", req_grad: bool = False) -> Tensor:
    if mode not in {"fan_in", "fan_out"}:
        raise ValueError("mode must be either 'fan_in' or 'fan_out'.")
    fan_in, fan_out = _calculate_fan_in_and_fan_out(*shape)
    fan = fan_in if mode == "fan_in" else fan_out
    std = (2 / fan) ** 5
    return ad.random.randn(*shape, mean=0, std=std, device=get_nn_device(), req_grad=req_grad)
