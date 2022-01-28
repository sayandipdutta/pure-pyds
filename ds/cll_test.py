import pytest
from .cll import CLList

def test_append():
    """Test append method of CLL class"""
    cll = CLList()
    cll.append(1)
    assert cll.size == 1
    assert cll.head.value == 1
    assert cll.tail.value == 1
    cll.append(2)
    assert cll.size == 2
    assert cll.head.value == 1
    assert cll.tail.value == 2
    cll.append(3)
    assert cll.size == 3
    assert cll.head.value == 1
    assert cll.tail.value == 3

def test_appendleft():
    """Test appendleft method of CLL class"""
    cll = CLList()
    cll.appendleft(1)
    assert cll.size == 1
    assert cll.head.value == 1
    assert cll.tail.value == 1
    cll.appendleft(2)
    assert cll.size == 2
    assert cll.head.value == 2
    assert cll.tail.value == 1
    cll.appendleft(3)
    assert cll.size == 3
    assert cll.head.value == 3
    assert cll.tail.value == 1

def test_getitem():
    """Test getitem method of CLL class"""
    cll = CLList()
    cll.appendleft(1)
    cll.appendleft(2)
    cll.appendleft(3)
    assert cll[0] == 3
    assert cll[1] == 2
    assert cll[2] == 1
    assert cll[-1] == 1

    with pytest.raises(IndexError):
        cll[3]

def test_setitem():
    """Test setitem method of CLL class"""
    cll = CLList()
    cll.appendleft(1)
    cll.appendleft(2)
    cll.appendleft(3)
    cll[0] = 6
    cll[1] = 5
    cll[2] = 4
    assert cll[0] == 6
    assert cll[1] == 5
    assert cll[2] == 4
    assert cll[-1] == 4

    with pytest.raises(IndexError):
        cll[3] = 7

def test_from_iterable():
    """Test from_iterable method of CLL class"""
    cll = CLList.from_iterable([1, 2, 3])
    assert cll.size == 3
    assert cll.head.value == 1
    assert cll.tail.value == 3