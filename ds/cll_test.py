import pytest
from .cll import CLList
from .errors import InvalidIntegerSliceError

@pytest.fixture
def list_data():
    """Return a CLL object"""
    return list(range(10))

@pytest.fixture
def cll_data():
    """Return a CLL object"""
    return CLList(range(10))

@pytest.mark.parametrize("value, is_error", [
    (slice(2, 10), False),
    (slice(2, 10, 2), False),
    (slice(2, 10, 3), False),
    (slice(None, None, -1), False),
    (slice(-2, -10, -1), False),
    (slice(10, 2, -1), False),
    (slice(-2, -10, 'v'), InvalidIntegerSliceError),
    (12, IndexError), 
    (-5, False)
])
def test_getitem(list_data, cll_data, value, is_error):
    """Test getitem method of CLL class"""
    if is_error:
        with pytest.raises(is_error):
            cll_data[value]
    else:
        val = cll_data[value]
        if isinstance(val, int):
            assert val == list_data[value]
        else:
            assert list(cll_data[value]) == list_data[value]

def test_cll(cll_data):
    """Test cll method of CLL class"""
    assert list(cll_data)== [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    assert cll_data.size == 10

def test_lshift(cll_data):
    """Test lshift method of CLL class"""
    assert cll_data.head.value == 0
    assert cll_data.tail.value == 9
    cll_data << 1
    assert cll_data.head.value == 9
    assert cll_data.tail.value == 8

def test_rshift(cll_data):
    """Test rshift method of CLL class"""
    assert cll_data.head.value == 0
    assert cll_data.tail.value == 9
    cll_data >> 1
    assert cll_data.head.value == 1
    assert cll_data.tail.value == 0

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

def test_from_iterable():
    """Test from_iterable method of CLL class"""
    cll = CLList.from_iterable([1, 2, 3])
    assert cll.size == 3
    assert cll.head.value == 1
    assert cll.tail.value == 3