from collections.abc import MutableSequence
# from dataclasses import dataclass, field
from typing import Generic, Iterator, Literal, Optional, TypeVar, overload

T = TypeVar("T")


class EmptyInstanceHeadAccess(ValueError, IndexError):
    def __init__(self, *args, hint: str='', **kwargs):
        super().__init__(*args, **kwargs)
        self.hint = f'\nHint: {hint}' * bool(hint)


class Node(Generic[T]):
    __slots__ = ('value', 'left', 'right')

    def __init__(self, value: T):
        self.value: T = value
        self.left: 'Node[T]' = self
        self.right: 'Node[T]' = self

    @classmethod
    def with_node(
            cls, 
            value: T, 
            *, 
            left: 'Node[T]', 
            right: 'Node[T]'
        ) -> 'Node[T]':
        self = cls(value)
        self.left, self.right = left, right
        return self


class CLList(MutableSequence[T]):

    __slots__ = ('_head', '_size')
    # @TODO: Add assert_types
    def __init__(self, value: T=None):
        if value is not None:
            self._head: Node[T] = Node(value)
        self._size: int = 0

    @property
    def size(self) -> int:
        return self._size

    @size.setter
    def size(self, value: int):
        if value < 0:
            raise ValueError("Size must be non-negative")
        if value == 0 and hasattr(self, '_head'):
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

    @property
    def tail(self) -> Node[T]:
        if self.size == 0:
            raise EmptyInstanceHeadAccess(
                "Cannot get tail of empty CLList",
                hint = "Try inserting an item first using append()/appendleft()"
            )
        return self.head.left

    def __len__(self) -> int:
        return self.size

    @overload
    def peek(self, index: int, /, *, node: Literal[True], errors: Literal['raise']) -> Node[T]:
        """If node is True, return Node at given index.
        If errors is 'raise':
            If index is out of bounds raises IndexError.
            If invalid error type, raises ValueError.
        """

    @overload
    def peek(self, index: int, /, *, node: Literal[False], errors: Literal['raise']) -> T:
        """If node is False, return value at given index.
        If errors is 'raise':
            If index is out of bounds raises IndexError.
            If invalid error type, raises ValueError.
        """

    @overload
    def peek(self, index: int, /, *, node: Literal[True], errors: Literal['ignore']) -> Node[T] | None:
        """If node is True, return Node at given index.
        If errors is 'ignore':
            If index is out of bounds return None.
            If invalid error type, raises ValueError.
        """

    @overload
    def peek(self, index: int, /, *, node: Literal[False], errors: Literal['ignore']) -> T | None:
        """If node is False, return value at given index.
        If errors is 'ignore':
            If index is out of bounds return None.
            If invalid error type, raises ValueError.
        """

    def peek(self, index: int, /, *, node: bool=True, errors: Literal['ignore', 'raise'] = 'ignore') -> T | Node[T] | None:
        """Return item at given index, or None if index is out of range.
        If node is True, return the node at the given index.
        If errors is 'raise', raise IndexError if index is out of range.
        If errors is 'ignore', return None if index is out of range.
        default is 'ignore'.
        """
        if index < 0:
            index += self.size
        if index < 0 or index >= self.size:
            if errors == 'ignore':
                return None
            elif errors == 'raise':
                raise IndexError(f"Index {index} out of range")
            else:
                raise ValueError(f"Unknown errors value: {errors}. Must be 'raise' or 'ignore'")

        if (reverse := (index > self.size//2)):
            index = self.size - index - 1
        for i, i_node in enumerate(self.iter_nodes(reverse=reverse)):
            if i == index:
                return i_node.value if node else i_node
        return None

    def pop(self, index: int = -1) -> T:
        """Remove and return item at given index.
        If index is None, remove and return last item.
        If index is out of range, raise IndexError.
        """
        if index < 0:
            index += self.size
        if index < 0 or index >= self.size:
            raise IndexError(f"Index {index} out of range")
        if self.size == 0:
            raise EmptyInstanceHeadAccess(
                "Cannot pop from empty CLList",
                hint = "Try inserting an item first using append()/appendleft()"
            )
        if self.size == 1:
            val = self.head.value
            self.size = 0
            return val
        if index == 0:
            return self.popleft()
        if index == self.size - 1:
            return self.pop()
        ith_node = self.peek(index, node=True, errors='raise')
        ith_node.left.right = ith_node.right
        ith_node.right.left = ith_node.left
        self.size -= 1
        return ith_node.value

    def popleft(self) -> T:
        """Remove and return first item, in doubly linked list.
        Raise EmptyInstanceHeadAccess if empty.
        """
        if self.size == 0:
            raise EmptyInstanceHeadAccess(
                "Cannot pop from empty CLList",
                hint = "Try inserting an item first using append()/appendleft()"
            )
        val = self.head.value
        if self.size == 1:
            self.size = 0
            return val
        self.head.right.left = self.head.left
        self.head = self.head.right
        self.size -= 1
        return val

    def insert(self, index: int, value: T):
        """Insert value at given index, in doubly linked list.
        If index is greater than size, raise IndexError.
        """
        if index < 0:
            index += self.size
        if index < 0 or index > self.size:
            raise IndexError(f"Index {index} out of range")
        if index == 0:
            self.appendleft(value)
            return
        if index == self.size:
            self.append(value)
            return
        
        ith_node = self.peek(index, node=True, errors='raise')
        ith_node.left.right = Node.with_node(value, left=ith_node.left, right=ith_node)
        ith_node.left = ith_node.right
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

    def append(self, value: T):
        """Insert value at the end of the list.
        """
        if self.size == 0:
            self.head = Node(value)
        else:
            node = Node.with_node(value, left=self.tail, right=self.tail.right)
            self.tail.right.left = node
            self.tail.right = node
        self.size += 1

    def iter_nodes(self, cycle: bool = False, reverse: bool = False) -> Iterator[Node[T]]:
        if self.size == 0:
            return 'Empty CLList'

        current = self.head
        while True:
            yield current
            current = current.left if reverse else current.right    # determine direction
            if not cycle and current is self.head:                  # break if not cyclic
                break

    def __iter__(self) -> Iterator[T]:
        for node in self.iter_nodes():
            yield node.value

    def __reversed__(self) -> Iterator[T]:
        for node in self.iter_nodes(reverse=True):
            yield node.value
    
    

    # @overload
    # def __getitem__(self, index: int) -> T:
    #     pass

    # @overload
    # def __getitem__(self, index: slice) -> 'CLList[T]':
    #     pass