from collections.abc import MutableSequence, Iterable
from itertools import chain
from typing import (
    Any,
    Generic, 
    Iterator, 
    Literal,
    Optional,
    TypeVar, 
    overload
)

from .errors import EmptyInstanceHeadAccess, InvalidIntegerSliceError
from .types import _SupportsComparison
from .validate import _validate_integer_slice, assert_types

T = TypeVar("T")
C = TypeVar("C", bound=_SupportsComparison)

class Node(Generic[T]):
    __slots__ = ('_value', '_left', '_right')

    def __init__(self, value: T, left: 'Node[T]' = None, right: 'Node[T]' = None):
        self._value: T = value
        self._left: 'Node[T]' = self if left is None else left
        self._right: 'Node[T]' = self if right is None else right

    @property
    def value(self) -> T:
        return self._value

    @value.setter
    def value(self, value: T):
        self._value = value

    @property
    def left(self) -> 'Node[T]':
        return self._left

    @left.setter
    def left(self, left: 'Node[T]'):
        if not isinstance(left, self.__class__) and left is not None:
            raise TypeError(f'left must be of type {self.__class__.__name__}')
        self._left = self if left is None else left

    @property
    def right(self) -> 'Node[T]':
        return self._right

    @right.setter
    def right(self, right: 'Node[T]'):
        if not isinstance(right, self.__class__) and right is not None:
            raise TypeError(f'right must be of type {self.__class__.__name__}')
        self._right = self if right is None else right

    def __eq__(self, other: Any):
        return isinstance(other, self.__class__) and self.value == other.value

    def __ne__(self, other: Any):
        return not self.__eq__(other)

    def __lt__(self: 'Node[C]', other: 'Node[C]') -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.value < other.value

    def __gt__(self: 'Node[C]', other: 'Node[C]') -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.value > other.value

    def __ge__(self: 'Node[C]', other: 'Node[C]') -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.value >= other.value

    def __le__(self: 'Node[C]', other: 'Node[C]') -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.value <= other.value

    def __rich_repr__(self):
        yield 'value', self.value
        yield 'left', self.__class__
        yield 'right', self.__class__

    __rich_repr__.angular = True    # type: ignore

    def __repr__(self):
        return (
            f'{self.__class__.__name__}('
            + ', '.join(f'{k}={v!r}' for k, v in self.__rich_repr__())
            + ')'
        )


class CLList(MutableSequence[T]):

    __slots__ = ('_head', '_size')
    
    def __init__(self, value: Optional[T | Iterable[T]] = None):
        self._head: Node[T]
        self._size: int = 0
        if isinstance(value, Iterable):
            new = self.__class__.from_iterable(value)
            if new:
                self._head = new.head
                self._size = new.size
            return
        if value is not None:
            self._head = Node(value)
            self._size += 1

    @classmethod
    @assert_types(iterable=Iterable)
    def from_iterable(cls, iterable: Iterable[T]) -> 'CLList[T]':
        self = cls()
        for item in iterable:
            self.append(item)
        return self

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
                hint = "Try inserting an item first "
                       "using append()/appendleft()."
            )
        return self._head

    @head.setter
    def head(self, value: Node[T]):
        if not isinstance(value, Node):
            raise ValueError(f"Head must be Node. Got {type(value)=}")
        self._head = value

    @property
    def tail(self) -> Node[T]:
        if self.size == 0:
            raise EmptyInstanceHeadAccess(
                "Cannot get tail of empty CLList",
                hint = "Try inserting an item first "
                       "using append()/appendleft()."
            )
        return self.head.left

    def clear(self) -> None:
        self.size = 0

    def copy(self) -> 'CLList[T]':
        return self.__class__.from_iterable(self)

    def __len__(self) -> int:
        return self.size

    @overload
    def peek(
            self, 
            index: int, 
            /, 
            *, 
            node: Literal[True], 
            errors: Literal['raise']
            ) -> Node[T]:
        """If node is True, return Node at given index.
        If errors is 'raise':
            If index is out of bounds raises IndexError.
            If invalid error type, raises ValueError.
        """

    @overload
    def peek(
            self, 
            index: int, 
            /, 
            *, 
            node: Literal[False], 
            errors: Literal['raise']
            ) -> T:
        """If node is False, return value at given index.
        If errors is 'raise':
            If index is out of bounds raises IndexError.
            If invalid error type, raises ValueError.
        """

    @overload
    def peek(
            self, 
            index: int, 
            /, 
            *, 
            node: Literal[True], 
            errors: Literal['ignore']
            ) -> Node[T] | None:
        """If node is True, return Node at given index.
        If errors is 'ignore':
            If index is out of bounds return None.
            If invalid error type, raises ValueError.
        """

    @overload
    def peek(
            self, 
            index: int, 
            /, 
            *, 
            node: Literal[False], 
            errors: Literal['ignore']
            ) -> T | None:
        """If node is False, return value at given index.
        If errors is 'ignore':
            If index is out of bounds return None.
            If invalid error type, raises ValueError.
        """

    @assert_types(index=int)
    def peek(
            self, 
            index: int, 
            /, 
            *, 
            node: bool=False, 
            errors: Literal['ignore', 'raise'] = 'ignore'
            ) -> T | Node[T] | None:
        """Return item at given index, or None if index is out of range.
        If node is True, return the node at the given index.
        If errors=='raise', raise IndexError if index is out of range.
        If errors=='ignore', return None if index is out of range.
        default is 'ignore'.
        """
        if index < 0:               # Handle negative index
            index += self.size
        if index < 0 or index >= self.size:
            if errors == 'ignore':
                return None
            elif errors == 'raise':
                raise IndexError(f"Index {index} out of range")
            else:
                raise ValueError(
                    f"Unknown errors value: {errors}. "
                    "Must be 'raise' or 'ignore'"
                )

        # determine shortest direction to index
        if (reverse := (index > self.size//2)):
            index = self.size - index - 1       # adjust index
        for i, i_node in enumerate(self.iter_nodes(reverse=reverse)):
            if i == index:
                return i_node if node else i_node.value
        return None

    @assert_types(index=int)
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

    @assert_types(index=int)
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
        ith_node.left.right = Node(
            value, 
            left=ith_node.left, 
            right=ith_node
        )
        ith_node.left = ith_node.right
        self.size += 1

    def appendleft(self, value: T):
        """Insert value at the front of the list.
        """
        if self.size == 0:
            self.head = Node(value)
        else:
            node = Node(
                value, 
                left=self.head.left, 
                right=self.head
            )
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
            node = Node(
                value, 
                left=self.tail, 
                right=self.head
            )
            self.tail.right = node
            self.head.left = node
        self.size += 1

    @assert_types(values=Iterable)
    def extend(self, values: Iterable[T]) -> None:
        """Insert values at the end of the list.
        """
        new = self.__class__.from_iterable(values)
        if new.size == 0:
            return
        if self.size == 0:
            self.head = new.head
            self.size = new.size
            return
        self.head.left.right = new.head
        new.head.left = self.head.left
        self.head.left = new.tail
        new.tail.right = self.head
        self.size += new.size
        del new # free memory

    def iter_nodes(
            self, 
            cycle: bool = False, 
            reverse: bool = False
        ) -> Iterator[Node[T]]:
        if self.size == 0:
            return 'Empty CLList'

        current = self.tail if reverse else self.head
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

    @overload
    def __getitem__(self, index: int) -> T:
        """If index is int, return item at given index.
        If index is out of range, raise IndexError.
        """

    @overload
    def __getitem__(self, index: slice) -> 'CLList[T]':
        """If index is slice, return a new CLList with items in given range.
        """

    @assert_types(index = int | slice)
    def __getitem__(self, index):
        if isinstance(index, int):
            try:
                return self.peek(index, node=False, errors='raise')
            except IndexError:
                raise IndexError(
                    f"{index=} out of range, "
                    "for CLList of {len(self)=} items"
                )
        
        # slice
        err = _validate_integer_slice(index)
        if err is not None:
            raise InvalidIntegerSliceError(err) from None

        start, stop, step = index.indices(self.size)
        
        return self.__class__.from_iterable(
                self[i] for i in range(start, stop, step)
            )
    
    @overload
    def __setitem__(self, index: int, value: T):
        """If index is int, set item at given index to value.
        If index is out of range, raise IndexError.
        """

    @overload
    def __setitem__(self, index: slice, value: Iterable[T]):
        """If index is slice, set items in given range to values.
        If extended slice length is greater than value length, 
        raise ValueError.
        """

    def __setitem__(self, index, value):
        if isinstance(index, int):
            try:
                self.peek(index, node=True, errors='raise').value = value
                return
            except (IndexError, ValueError) as exc:
                # @TODO: add logging
                raise exc from None

        # handle slice
        err = _validate_integer_slice(index)
        if err is not None:
            raise InvalidIntegerSliceError(err) from None

        points = range(*index.indices(self.size))
        slice_size = len(points)

        if slice_size == self.size:
            self.clear()
            self.extend(value)
            return
        # breakpoint()
        start, stop, step = points.start, points.stop, points.step
        new = self.__class__.from_iterable(value)
        if step == 1:
            del self[start:stop:step]
            if new.size == 0:
                del new
                return
            set_after = self.peek(start - 1, node=True, errors='raise')
            set_until = set_after.right
            set_after.right = new.head
            set_until.left = new.tail
            new.tail.right = set_until
            new.head.left = set_after
            if 0 in points:
                self.head = new.head
            self.size += new.size
            del new
            return

        # handle extended slice
        if slice_size != len(new):
            raise ValueError(
                f"attempt to assign sequence of size {len(new)} "
                f"to extended slice of size {slice_size}"
            )
        # breakpoint()
        for i, value in zip(points, value, strict=True):
            self[i] = value

    @assert_types(index = int | slice)
    def __delitem__(self, index: int | slice):
        if isinstance(index, int):
            try:
                self.pop(index)
                return
            except IndexError as exc:
                # @TODO: Add logging.
                raise exc from None

        # handle slice
        err = _validate_integer_slice(index)
        if err is not None:
            raise InvalidIntegerSliceError(err) from None

        points = range(*index.indices(self.size))
        slice_size = len(points)

        if slice_size == self.size:
            self.clear()
            return

        if slice_size == 0 or self.size == 0:
            return

        start, stop, step = points.start, points.stop, points.step

        if step == 1 or step == -1:
            start, stop = (start, stop - 1) if step == 1 else (stop + 1, start)
            del_from = self.peek(start, node=True, errors='raise')
            del_till = self.peek(stop, node=True, errors='raise')
            del_from.left.right = del_till.right
            del_till.right.left = del_from.left
            self.size -= slice_size

            # assign correct head if head was deleted
            if 0 in points and self.size > 0:
                self.head = del_till.right
            return
            
        # handle extended slice
        for i in points:
            self.pop(i)

    @assert_types(by=int)
    def __rshift__(self, by: int) -> 'CLList[T]':
        """Return a new CLList with items shifted by given amount.
        If amount is negative, shift items to left.
        If amount is greater than length of CLList, return empty CLList.
        """
        if by == 0:
            return self.copy()
        if by < 0:
            return self << -by
        if by >= self.size:
            return self or (self >> (by % self.size))
        self.head = self.peek(by, node=True, errors='raise')
        return self

    @assert_types(by=int)
    def __lshift__(self, by: int) -> 'CLList[T]':
        """Return a new CLList with items shifted by given amount.
        If amount is negative, shift items to right.
        If amount is greater than length of CLList, return empty CLList.
        """
        if by == 0:
            return self.copy()
        if by < 0:
            return self >> -by
        if by >= self.size:
            return self or (self << (by % self.size))
        return self

    def __eq__(self, __o: Any) -> bool:
        return all(
            s == __o.peek(i) for i, s in enumerate(self)
        )

    def __ne__(self, __o: Any) -> bool:
        return not self == __o

    def __lt__(self, __o: 'CLList[Any]') -> bool:
        if not isinstance(__o, type(self)):
            return NotImplemented
        return self.size < __o.size if (self.size and __o.size) else True

    def __le__(self, __o: 'CLList[Any]') -> bool:
        if not isinstance(__o, type(self)):
            return NotImplemented
        return self.size <= __o.size if (self.size and __o.size) else True

    def __gt__(self, __o: 'CLList[Any]') -> bool:
        if not isinstance(__o, type(self)):
            return NotImplemented
        return self.size > __o.size if (self.size and __o.size) else False

    def __ge__(self, __o: 'CLList[Any]') -> bool:
        if not isinstance(__o, type(self)):
            return NotImplemented
        return self.size >= __o.size if (self.size and __o.size) else False
        
    def __repr__(self) -> str:
        debug_size = sum(1 for _ in self)
        if (size := self.size) == 0:
            return f'{self.__class__.__name__}(empty, size=0, {debug_size=})'
        return f'{self.__class__.__name__}(head={self.head}, {size=}, {debug_size=})'

    def __rich_repr__(self):
        yield "empty" if self.size == 0 else ("head", self.head)
        yield "size", self.size

    __rich_repr__.angular = True    # type: ignore

if __name__ == '__main__':
    n = Node(9)
    l = Node(10)
    print(l > n)