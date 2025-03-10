from abc import ABC, abstractmethod
from typing import Any, Optional

from emgrad._backends import Device
from emgrad.dtypes import ArrayLike


class Op(ABC):
    def __init__(self, device: Device, **kwargs: Any) -> None:
        self.xp = device.xp
        self.kwargs = kwargs
        self._cache: Any = None

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def save_to_cache(self, *args: Any):
        self._cache = args

    def retrieve_from_cache(self) -> tuple[Any, ...]:
        assert self._cache is not None
        values, self._cache = self._cache, None
        return values

    @abstractmethod
    def forward(self, *arrays: Optional[ArrayLike], **kwargs: Any) -> ArrayLike:
        raise NotImplementedError("Subclasses must implement the forward method.")

    @abstractmethod
    def backward(self, dy: ArrayLike) -> tuple[Any, ...]:
        raise NotImplementedError("Subclasses must implement the backward method.")
