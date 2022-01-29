from collections.abc import MutableSequence, Iterable
import doctest
from itertools import chain
from typing import (
    Any,
    Generic, 
    Iterator, 
    Literal,
    Optional,
    TypeVar,
    cast, 
    overload
)

from .errors import EmptyInstanceHeadAccess, InvalidIntegerSliceError
from .types import _SupportsComparison, MissingType
from .validate import _validate_integer_slice, assert_types

T = TypeVar("T")
C = TypeVar("C", bound=_SupportsComparison)

_missing = MissingType()

class Node(Generic[T]):
    """Class implementing Node. 
    
    It has three properties:
    - value: T - the value of the node
    - left: Node[T] - the left item of the node
    - right: Node[T] - the right item of the node

    All the properties are undeleteable.
    Only a Node object can be assigned to the left and right properties.

    For Node initialized with only value, both left and right point to
    itself.

    Usage:
        >>> from ds.cdll import Node
        >>> node = Node(1)
        >>> node
        Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>)
        >>> node.value
        1
        >>> node.left
        Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>)
        >>> node.right is node.left
        True
        >>> node.left = Node(2)
        >>> node.left
        Node(value=2, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>)
        >>> node.right = Node(3)
        >>> node.right
        Node(value=3, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>)
        >>> node.left < node.right
        True
        >>> # checks (node.left.value := 2) < (node.right.value := 3) == True
        >>> node > node.right
        False
    """
    __slots__ = ('_value', '_left', '_right')

    def __init__(self, value: T, *, left: 'Node[T]' = None, right: 'Node[T]' = None):
        """Node(value, *[, left, right]) -> Node[T]

        Args:
            value (T): [description]
            left (Node[T], optional): [description]. Defaults to None.
            right (Node[T], optional): [description]. Defaults to None.
        """
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
        """Add support for rich representation.
        
        See [1], [2] in CDLL.__rich_repr__() docstring for more details.
        """
        yield 'value', self.value
        yield 'left', self.__class__
        yield 'right', self.__class__

    # See [1], [2] in CDLL.__rich_repr__() docstring for more details.
    __rich_repr__.angular = True    # type: ignore

    def __repr__(self):
        return (
            f'{self.__class__.__name__}('
            + ', '.join(f'{k}={v!r}' for k, v in self.__rich_repr__())
            + ')'
        )


class CDLList(MutableSequence[T]):
    """Class implementing Circular Doubly Linked List.
    
    
    This class implements a circular doubly linked list
    https://en.wikipedia.org/wiki/Doubly_linked_list#Circular_doubly_linked_lists

    The class constructor takes either a single value and initializes the list
    by setting the head to a Node with the value and both left and right to
    itself, or a sequence of values and initializes the list by setting the
    head to a Node with the first value and both left and right to a Node with
    the second value and so on. When no values are given, the head attribute is not set.
    Furthermore, if the sequence is empty, the head attribute is inaccessible.
    Trying to access head on a empty CDLList instance with raise
    ds.errors.EmptyInstanceHeadAccess exception.

    When the list is empty, i.e., size is 0, there is no head / tail.

    Usage:
        >>> from ds.cdll import CDLList
        >>> cdll = CDLList(1)
        >>> cdll
        CDLList(head=Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=1)
        >>> cdll.append(2)
        >>> cdll
        CDLList(head=Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=2)
        >>> cdll.head
        Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>)
        >>> cdll.head.left
        Node(value=2, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>)
        >>> list(cdll)
        [1, 2]
        >>> cdll.pop()
        2
        >>> list(cdll[:2])
        [1]
        >>> CDLList([1, 2, 3, 4, 5])
        CDLList(head=Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=5)
    """

    __slots__ = ('_head', '_size')
    
    def __init__(self, value: T | Iterable[T] | MissingType = _missing):
        """value can be a single value or an iterable of values."""
        self._head: Node[T]
        self._size: int = 0
        if isinstance(value, Iterable):
            new = self.__class__.from_iterable(value)
            if new:
                self._head = new.head
                self._size = new.size
            return
        if value is not _missing:
            self._head = Node(cast(T, value))
            self._size += 1

    @classmethod
    @assert_types(iterable=Iterable)
    def from_iterable(cls, iterable: Iterable[T]) -> 'CDLList[T]':
        """Creates a CDLList from an iterable."""
        self = cls()
        for item in iterable:
            self.append(item)
        return self

    @property
    def size(self) -> int:
        """Property: Size of the CDLList."""
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
        """Property: Head of the CDLList."""
        if self.size == 0:
            raise EmptyInstanceHeadAccess(
                "Cannot get head of empty CDLList",
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
        """Property: Tail of the CDLList."""
        if self.size == 0:
            raise EmptyInstanceHeadAccess(
                "Cannot get tail of empty CDLList",
                hint = "Try inserting an item first "
                       "using append()/appendleft()."
            )
        return self.head.left

    def clear(self) -> None:
        """Clears the CDLList. i.e. removes all items.
        
        Usage:
            >>> from ds.cdll import CDLList
            >>> cdll = CDLList([1, 2, 3])
            >>> cdll
            CDLList(head=Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=3)
            >>> cdll.clear()
            >>> cdll
            CDLList(empty, size=0)
        """
        self.size = 0

    def copy(self) -> 'CDLList[T]':
        """Returns a shallow copy of the CDLList.
        
        Usage:
            >>> from ds.cdll import CDLList
            >>> cdll = CDLList([1, 2, 3])
            >>> cdll
            CDLList(head=Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=3)
            >>> cdll2 = cdll.copy()
            >>> cdll2
            CDLList(head=Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=3)
            >>> cdll2 is cdll
            False
        """
        return self.__class__.from_iterable(self)

    def __len__(self) -> int:
        """Returns the size, i.e. length of the CDLList.
        
        Usage:
            >>> from ds.cdll import CDLList
            >>> cdll = CDLList([1, 2, 3])
            >>> cdll
            CDLList(head=Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=3)
            >>> len(cdll)
            3
        """
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

        Usage:
            >>> from ds.cdll import CDLList
            >>> cdll = CDLList([1, 2, 3])
            >>> cdll
            CDLList(head=Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=3)
            >>> cdll.peek(0)
            1
            >>> cdll.peek(1, node=True)
            Node(value=2, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>)
            >>> cdll.peek(3)
            >>> cdll.peek(3, node=True)
            >>> cdll.peek(3, node=True, errors='raise')
            Traceback (most recent call last):
                ...
            IndexError: Index 3 out of range.
            >>> cdll.peek(3, node=True, errors='ignore') is None
            True
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

        Usage:
            >>> from ds.cdll import CDLList
            >>> cdll = CDLList([1, 2, 3])
            >>> cdll
            CDLList(head=Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=3)
            >>> cdll.pop(0)
            1
            >>> cdll
            CDLList(head=Node(value=2, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=2)
            >>> cdll.pop(1)
            3
            >>> cdll
            CDLList(head=Node(value=2, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=1)
            >>> cdll.pop(1)
            Traceback (most recent call last):
                ...
            IndexError: Index 1 out of range.
        """
        if index < 0:
            index += self.size
        if index < 0 or index >= self.size:
            raise IndexError(f"Index {index} out of range")
        if self.size == 0:
            raise EmptyInstanceHeadAccess(
                "Cannot pop from empty CDLList",
                hint = "Try inserting an item first using append()/appendleft()"
            )
        if self.size == 1:
            val = self.head.value
            self.size = 0
            return val
        if index == 0:
            return self.popleft()
        ith_node = self.peek(index, node=True, errors='raise')
        ith_node.left.right = ith_node.right
        ith_node.right.left = ith_node.left
        self.size -= 1
        return ith_node.value

    def popleft(self) -> T:
        """Remove and return first item, in doubly linked list.
        Raise EmptyInstanceHeadAccess if empty.

        Usage:
            >>> from ds.cdll import CDLList
            >>> cdll = CDLList([1])
            >>> cdll
            CDLList(head=Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=1)
            >>> cdll.popleft()
            1
            >>> cdll
            CDLList(empty, size=0)
            >>> cdll.popleft()
            Traceback (most recent call last):
                ...
            ds.errors.EmptyInstanceHeadAccess: Cannot pop from empty CDLList
            Hint: Try inserting an item first using append()/appendleft()
        """
        if self.size == 0:
            raise EmptyInstanceHeadAccess(
                "Cannot pop from empty CDLList",
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

        Usage:
            >>> from ds.cdll import CDLList
            >>> cdll = CDLList([1, 2, 3])
            >>> cdll
            CDLList(head=Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=3)
            >>> cdll.insert(0, 0)
            >>> list(cdll)
            [0, 1, 2, 3]
            >>> cdll.insert(2, 0)
            >>> list(cdll)
            [0, 1, 0, 2, 3]
            >>> cdll
            CDLList(head=Node(value=0, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=5)
            >>> cdll.insert(9, 0)
            Traceback (most recent call last):
                ...
            IndexError: Index 9 out of range.
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

        Moves head to the newly inserted node.

        Usage:
            >>> from ds.cdll import CDLList
            >>> cdll = CDLList([])
            >>> cdll
            CDLList(empty, size=0)
            >>> cdll.appendleft(1)
            >>> cdll
            CDLList(head=Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=1)
            >>> cdll.appendleft(2)
            >>> cdll
            CDLList(head=Node(value=2, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=2)
            >>> list(cdll)
            [2, 1]
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

        Usage:
            >>> from ds.cdll import CDLList
            >>> cdll = CDLList([])
            >>> cdll
            CDLList(empty, size=0)
            >>> cdll.append(1)
            >>> cdll
            CDLList(head=Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=1)
            >>> cdll.append(2)
            >>> cdll
            CDLList(head=Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=2)
            >>> list(cdll)
            [1, 2]
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

        Usage:
            >>> from ds.cdll import CDLList
            >>> cdll = CDLList([])
            >>> cdll.extend([1, 2, 3])
            >>> cdll
            CDLList(head=Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=3)
            >>> list(cdll)
            [1, 2, 3]
            >>> cdll.extend([4, 5, 6])
            >>> cdll
            CDLList(head=Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=6)
            >>> list(cdll)
            [1, 2, 3, 4, 5, 6]
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
        r"""Iterate over nodes in the list.

        If cycle is True, iterate over nodes in a cycle. (default: False)
        If reverse is True, iterate over nodes in reverse order. (default: False)

        Usage:
            >>> from ds.cdll import CDLList
            >>> cdll = CDLList([1, 2, 3])
            >>> print(*cdll.iter_nodes(), sep='\n')
            Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>)
            Node(value=2, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>)
            Node(value=3, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>)
            >>> print(*cdll.iter_nodes(reverse=True), sep='\n')
            Node(value=3, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>)
            Node(value=2, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>)
            Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>)
        """
        if self.size == 0:
            return 'Empty CDLList'

        current = self.tail if reverse else self.head
        while True:
            yield current
            current = current.left if reverse else current.right    # determine direction
            if not cycle and current is self.head:                  # break if not cyclic
                break
        if reverse:
            yield self.head

    def __iter__(self) -> Iterator[T]:
        r"""Iterate over values in the list.

        Usage:
            >>> from ds.cdll import CDLList
            >>> cdll = CDLList([1, 2, 3])
            >>> print(*cdll, sep='\n')
            1
            2
            3
        """
        for node in self.iter_nodes():
            yield node.value

    def __reversed__(self) -> Iterator[T]:
        r"""Iterate over values in the list in reverse order.

        Usage:
            >>> from ds.cdll import CDLList
            >>> cdll = CDLList([1, 2, 3])
            >>> print(*reversed(cdll), sep='\n')
            3
            2
            1
        """
        for node in self.iter_nodes(reverse=True):
            yield node.value

    @overload
    def __getitem__(self, index: int) -> T:
        """If index is int, return item at given index.
        If index is out of range, raise IndexError.
        """

    @overload
    def __getitem__(self, index: slice) -> 'CDLList[T]':
        """If index is slice, return a new CDLList with items in given range.
        If slice is not a valid integer slice, raise InvalidIntegerSliceError.
        """

    @assert_types(index = int | slice)
    def __getitem__(self, index):
        """
        Return item(s) at given index(es).
        
        If index is int, return item at given index.
        If index is out of range, raise IndexError.
        If index is slice, return a new CDLList with items in given range.
        If slice is not a valid integer slice, raise InvalidIntegerSliceError.

        Usage:
            >>> from ds.cdll import CDLList
            >>> cdll = CDLList([1, 2, 3])
            >>> cdll[0]
            1
            >>> cdll[1]
            2
            >>> cdll[2]
            3
            >>> cdll[-1]
            3
            >>> cdll[3]
            Traceback (most recent call last):
            ...
            IndexError: list index out of range
            >>> cdll[1:2]
            CDLList(head=Node(value=2, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=1)
            >>> cdll[::-1]
            CDLList(head=Node(value=3, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=3)
            >>> cdll[:3:2]
            CDLList(head=Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=2)
            >>> list(cdll[:3:2])
            [1, 2]
            >>> cdll[::'w']
            Traceback (most recent call last):
            ...
            InvalidIntegerSliceError: slice indices must be integers or None or have an __index__ method
            Orig: <class 'TypeError'>
        """

        if isinstance(index, int):
            try:
                return self.peek(index, node=False, errors='raise')
            except IndexError:
                raise IndexError(
                    f"{index=} out of range, "
                    "for CDLList of {len(self)=} items"
                )
        
        # slice
        err = _validate_integer_slice(index)
        if err is not None:
            raise InvalidIntegerSliceError(orig=err) from None

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
        """
        Set item(s) at given index(es).

        If index is int, set item at given index to value.
        If index is out of range, raise IndexError.
        If index is slice, set items in given range to values.
        If extended slice length is greater than value length,
        raise ValueError.
        If slice is not a valid integer slice, raise InvalidIntegerSliceError.

        Usage:
            >>> from ds.cdll import CDLList
            >>> cdll = CDLList([1, 2, 3])
            >>> cdll[0] = 4
            >>> cdll[1] = 5
            >>> cdll[-1] = 7
            >>> cdll[3] = 8
            Traceback (most recent call last):
            ...
            IndexError: Index 3 out of range
            >>> cdll[1:2] = [9, 10]
            >>> list(cdll)
            [4, 9, 10, 7]
            >>> cdll[::-1] = [11, 12, 13, 14]
            >>> list(cdll)
            [14, 13, 12, 11]
            >>> cdll[:3:2] = [-1, -2]
            >>> list(cdll)
            [-1, 13, -2, 11]
            >>> cdll[::-1] = [15, 16]
            Traceback (most recent call last):
            ...
            ValueError: attempt to assign sequence of size 2 to extended slice of size 4
            >>> cdll[:] = []
            >>> list(cdll)
            []
        """
        # breakpoint()
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
            raise InvalidIntegerSliceError(orig=err) from None

        points = range(*index.indices(self.size))
        slice_size = len(points)
        start, stop, step = points.start, points.stop, points.step

        if slice_size == self.size and step == 1:
            self.clear()
            if step < 0:
                value = reversed(value)
            self.extend(value)
            return
        
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
        
        for i, value in zip(points, value, strict=True):
            self[i] = value

    @assert_types(index = int | slice)
    def __delitem__(self, index: int | slice):
        """If index is int, delete item at given index.
        If index is out of range, raise IndexError.
        If index is slice, delete items in given range.
        If slice is not a valid integer slice, raise InvalidIntegerSliceError.

        Usage:
            >>> from ds.cdll import CDLList
            >>> cdll = CDLList([1, 2, 3])
            >>> del cdll[0]
            >>> cdll
            CDLList(head=Node(value=2, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=2)
            >>> del cdll[:]
            >>> cdll
            CDLList(head=None, size=0)
        """
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
            raise InvalidIntegerSliceError(orig=err) from None

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
        # if start index is less than stop index, 
        # reverse the range to preserve order
        if points.start < points.stop:
            points = reversed(points)
        for i in points:
            self.pop(i)

    @assert_types(by=int)
    def __rshift__(self, by: int) -> 'CDLList[T]':
        """Moves head to right by given amount, 
        returns the CDLList with items shifted by given amount.

        Modifies in-place.

        If amount is negative, shift items to left.
        If amount is greater than length of CDLList, take a modulo of by
        w.r.t self.size, then apply lshift.

        Usage:
            >>> from ds.cdll import CDLList
            >>> cdll = CDLList([1, 2, 3])
            >>> cdll
            CDLList(head=Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=3)
            >>> cdll.head
            Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>)
            >>> cdll >> 2
            CDLList(head=Node(value=3, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=3)
            >>> cdll.head
            Node(value=3, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>)
            >>> cdll >> -2  # equivalent to cdll << 2
            CDLList(head=Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=3)
            >>> cdll.head
            Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>)
            >>> # cdll >> 4 is equivalent to: cdll >> 1 (because 4 % 3 == 1)
            >>> cdll >> 4
            CDLList(head=Node(value=2, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=3)
        """
        if by == 0:
            return self.copy()
        # if by negative, shift left by negative amount
        if by < 0:
            return self << -by
        # if shift is greater than length, shift by modulo
        if by >= self.size:
            return self or (self >> (by % self.size))
        # if shift is greater than half length, shift left by length - shift
        if by > self.size // 2:
            return self << (self.size - by)
        self.head = self.peek(by, node=True, errors='raise')
        return self

    @assert_types(by=int)
    def __lshift__(self, by: int) -> 'CDLList[T]':
        """Moves head to left by given amount,
        returns the CDLList with items shifted by given amount.

        Modifies in-place.

        If amount is negative, shift items to right.
        If amount is greater than length of CDLList, take a modulo of by
        w.r.t self.size, then apply rshift.

        Usage:
            >>> from ds.cdll import CDLList
            >>> cdll = CDLList([1, 2, 3])
            >>> cdll
            CDLList(head=Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=3)
            >>> cdll.head
            Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>)
            >>> cdll << 2
            CDLList(head=Node(value=2, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=3)
            >>> cdll.head
            Node(value=2, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>)
            >>> cdll << -2  # equivalent to cdll >> 2
            CDLList(head=Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=3)
            >>> cdll.head
            Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>)
            >>> # cdll << 4 is equivalent to: cdll << 1 (because 4 % 3 == 1)
            >>> cdll << 4
            CDLList(head=Node(value=3, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=3)
        """
        if by == 0:
            return self.copy()
        # if by negative, shift right by negative amount
        if by < 0:
            return self >> -by
        # if shift is greater than length, shift by modulo
        if by >= self.size:
            return self or (self << (by % self.size))
        # if shift is greater than half length, shift right by length - shift
        if by > self.size // 2:
            return self >> (self.size - by)
        self.head = self.peek(-by, node=True, errors='raise')
        return self

    def __contains__(self, x: Any) -> bool:
        """Check if value in CDLList.
        
        Usage:
            >>> from ds.cdll import CDLList
            >>> cdll = CDLList([1, 2, 3])
            >>> 2 in cdll
            True
            >>> 4 in cdll
            False
        """
        return any(x == value for value in self)

    @assert_types(value=int)
    def __floordiv__(self, value: int) -> list['CDLList[T]']:
        """Returns a list of equally size CDLList objects, 
        each containing a slice of self. Number of CDLLists 
        returned is equal to value.

        If value < 1, raises ValueError.
        
        Usage:
            >>> from ds.cdll import CDLList
            >>> cdll = CDLList([1, 2, 3, 4, 5, 6, 7, 8, 9])
            >>> cdll // 3
            [CDLList(head=Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=3),
             CDLList(head=Node(value=4, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=3),
             CDLList(head=Node(value=7, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=3)]
            >>> cdll // 2
            [CDLList(head=Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=4),
             CDLList(head=Node(value=5, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=4)]
            >>> cdll // 0
            Traceback (most recent call last):
                ...
            ValueError: value must be >= 1, not 0
        """

        if value < 1:
            raise ValueError(f"value must be >= 1, not {value}")
        if value > self.size:
            return [self.__class__()]
        result = []
        step = (self.size // value)
        stop = step * value
        points = range(0, stop, step)
        new = self.__class__()
        for i, val in enumerate(self):
            if i and i in points:
                result.append(new)
                new = self.__class__(val)
            else:
                new.append(val)
            if i + 1 == stop:
                result.append(new)
                break
        return result

    @assert_types(value=int)
    def __mod__(self, value: int) -> 'CDLList[T]':
        """Returns a CDLList containing a slice of self containing
        last n elements, where n == self.size % value.

        If value < 1, raises ValueError.

        Usage:
            >>> from ds.cdll import CDLList
            >>> cdll = CDLList([1, 2, 3, 4, 5, 6, 7, 8, 9])
            >>> cdll % 3
            CDLList(empty, size=0)
            >>> cdll % 2
            CDLList(head=Node(value=9, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=1)
            >>> cdll % 0
            Traceback (most recent call last):
                ...
            ValueError: value must be >= 1, not 0
        """
        if value < 1:
            raise ValueError(f"value must be >= 1, not {value}")
        if value > self.size:
            return self.copy()
        rem = self.size % value
        if rem:
            return self[-rem:]
        return self.__class__()

    @assert_types(value=int)
    def __divmod__(self, value: int) -> tuple[list['CDLList[T]'], 'CDLList[T]']:
        """Returns a tuple containing a two elements:
        1. self // value
        2. self % value

        If value < 1, raises ValueError.

        Usage:
            >>> from ds.cdll import CDLList
            >>> cdll = CDLList([1, 2, 3, 4, 5, 6, 7, 8, 9])
            >>> divmod(cdll, 3)
            ([CDLList(head=Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=3),
                CDLList(head=Node(value=4, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=3),
                CDLList(head=Node(value=7, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=3)],
                CDLList(head=Node(value=9, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=1))
            >>> divmod(cdll, 2)
            ([CDLList(head=Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=4),
                CDLList(head=Node(value=5, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=4)],
                CDLList(head=Node(value=9, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=1))
            >>> divmod(cdll, 0)
            Traceback (most recent call last):
                ...
            ValueError: value must be >= 1, not 0
        """

        if value < 1:
            raise ValueError(f"value must be >= 1, not {value}")
        return self // value, self % value

    @assert_types(value=Iterable)
    def __add__(self, other: Iterable[T]) -> 'CDLList[T]':
        """Return a new CDLList with items from self and other.

        Usage:
            >>> from ds.cdll import CDLList
            >>> cdll = CDLList([1, 2, 3])
            >>> cdll + [4, 5, 6]
            CDLList(head=Node(value=1, left=<class 'ds.cdll.Node'>, right=<class 'ds.cdll.Node'>), size=6)
            >>> list(cdll + [4, 5, 6])
            [1, 2, 3, 4, 5, 6]
        """
        return self.__class__(chain(self, other))

    def __eq__(self, other: Any) -> bool:
        """Return True if self and other are equal, False otherwise."""
        try:
            return (
                isinstance(other, CDLList)
                and self.size == other.size
                and all(
                    s == o for s, o in zip(self, other, strict=True)
                )
            )
        except ValueError:
            # this handles cases where 
            # other instance nodes are not linked properly
            # @TODO: add logging, add warning
            return False

    def __ne__(self, __o: Any) -> bool:
        """Return True if self and other are not equal, False otherwise."""
        return not self == __o

    def __lt__(self, __o: 'CDLList[Any]') -> bool:
        """Return True if self is less than other, False otherwise."""
        if not isinstance(__o, type(self)):
            return NotImplemented
        return self.size < __o.size if (self.size and __o.size) else True

    def __le__(self, __o: 'CDLList[Any]') -> bool:
        """Return True if self is less than or equal to other, False otherwise."""
        if not isinstance(__o, type(self)):
            return NotImplemented
        return self.size <= __o.size if (self.size and __o.size) else True

    def __gt__(self, __o: 'CDLList[Any]') -> bool:
        """Return True if self is greater than other, False otherwise."""
        if not isinstance(__o, type(self)):
            return NotImplemented
        return self.size > __o.size if (self.size and __o.size) else False

    def __ge__(self, __o: 'CDLList[Any]') -> bool:
        """Return True if self is greater than or equal to other, False otherwise."""
        if not isinstance(__o, type(self)):
            return NotImplemented
        return self.size >= __o.size if (self.size and __o.size) else False
        
    def __repr__(self) -> str:
        debug_size = sum(1 for _ in self)
        if (size := self.size) == 0:
            return f'{self.__class__.__name__}(empty, size=0)' #, {debug_size=})'
        return f'{self.__class__.__name__}(head={self.head}, {size=})' #, {debug_size=})'

    def __rich_repr__(self):
        """Add repr option for rich display.

        Reference: 
        1. https://github.com/willmcgugan/rich/tree/master/rich
        2. https://rich.readthedocs.io/en/stable/pretty.html#rich-repr-protocol
        """
        yield "empty" if self.size == 0 else ("head", self.head)
        yield "size", self.size

    # See: [1], [2] in __rich_repr__ docstring for more info
    __rich_repr__.angular = True    # type: ignore

if __name__ == '__main__':
    l: CDLList[int] = CDLList(range(1000))
    k = l[5:4:-1]
    q, r = divmod(l, 11)
    m = sorted(l)
    doctest.testmod()