from abc import abstractmethod
from typing import Protocol, TypeVar


C = TypeVar('C')

class _SupportsComparison(Protocol):
    @abstractmethod
    def __lt__(self: C, other: C) -> bool: ...
    @abstractmethod
    def __le__(self: C, other: C) -> bool: ...
    @abstractmethod
    def __gt__(self: C, other: C) -> bool: ...
    @abstractmethod
    def __ge__(self: C, other: C) -> bool: ...

class MissingType:
    '''Class to represent missing types'''
    pass