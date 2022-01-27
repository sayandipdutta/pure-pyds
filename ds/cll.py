from collections import MutableSequence
from dataclasses import dataclass, field
from typing import Generic, Iterator, TypeVar, overload

T = TypeVar("T")

class EmptyInstanceHeadAccess(ValueError, IndexError):
    def __init__(self, *args, hint: str='', **kwargs):
        super().__init__(*args, **kwargs)
        self.hint = f'\nHint: {hint}' * bool(hint)

@dataclass(slots=True)
class Node(Generic[T]):
    value: T
    left: 'Node[T]' = field(init=False)
    right: 'Node[T]' = field(init=False)

    def __post_init__(self):
        self.left = self
        self.right = self

    @classmethod
    def with_node(cls, value: T, *, left: 'Node[T]', right: 'Node[T]') -> 'Node[T]':
        return cls(value, left, right)


@dataclass(slots=True)
class CLList(MutableSequence[T]):
    _head: Node[T] = field(init=False)
    _size: int = field(init=False, default=0)

    @property
    def size(self) -> int:
        return self._size

    @size.setter
    def size(self, value):
        if value < 0:
            raise ValueError("Size must be non-negative")
        if value == 0:
            del self._head
        self._size = value

    @property
    def head(self) -> Node[T]:
        if self.size == 0:
            raise EmptyInstanceHeadAccess(
                "Cannot get head of empty CLList",
                hint = "Try inserting an item first using append()/appendleft()"
            )
        return self._head

    @head.setter
    def head(self, value: Node[T]):
        if not isinstance(value, Node):
            raise ValueError(f"Head must be a Node. Got {type(value)=}")
        self._head = value

    def __len__(self) -> int:
        return self.size

    def __iter__(self) -> Iterator[T]:
        if self.size == 0:
            return 'Empty CLList'
        current = self.head
        while current is not self.head:
            yield current.value
            current = current.right

    def insert(self, index: int, value: T):
        """Insert value at given index, in doubly linked list.
        If index is greater than size, raise IndexError.
        """
        if index < 0:
            index += self.size
        if index < 0 or index > self.size:
            raise IndexError(f"Index {index} out of range")
        if index == 0:
            self.insert_first(value)
            return
        current = self.head
        for _ in range(index):
            current = current.right
        current.left.right = Node.with_node(value, left=current.left, right=current)
        current.left = current.right
        self.size += 1

    def appendleft(self, value: T):
        """Insert value at the front of the list.
        """
        if self.size == 0:
            self.head = Node(value)
        else:
            node = Node.with_node(value, left=self.head.left, right=self.head)
            self.head.left.right = node
            self.head.left = node
            self.head = node
        self.size += 1

    

    @overload
    def __getitem__(self, index: int) -> T:
        pass

    @overload
    def __getitem__(self, index: slice) -> 'CLList[T]':
        pass

    def __getitem__(self, index):
        if isinstance(index, int):
            if index < 0:
                index += self.size
            if index < 0 or index >= self.size:
                raise IndexError(f"Index {index} out of range")
            current = self.head
            for _ in range(index):
                current = current.right
            return current.value
        elif isinstance(index, slice):
            start, stop, step = index.indices(self.size)
            if step == 1:
                return self.__class__.from_iterable(self[i] for i in range(start, stop))