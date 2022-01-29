import pytest
from .cdll import CDLList
from .errors import InvalidIntegerSliceError

@pytest.fixture
def list_data():
    """Return a CDLL object"""
    return list(range(10))

@pytest.fixture
def cdll_data():
    """Return a CDLL object"""
    return CDLList(range(10))

@pytest.fixture
def cdll_data_set():
    """Return a CDLL object"""
    return CDLList(range(10))

@pytest.fixture
def list_data_set():
    """Return a CDLL object"""
    return list(range(10))

@pytest.fixture
def cdll_data_del():
    """Return a CDLL object"""
    return CDLList(range(10))

@pytest.fixture
def list_data_del():
    """Return a CDLL object"""
    return list(range(10))

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
def test_getitem(list_data, cdll_data, value, is_error):
    """Test getitem method of CDLL class"""
    if is_error:
        with pytest.raises(is_error):
            cdll_data[value]
    else:
        val = cdll_data[value]
        if isinstance(val, int):
            assert val == list_data[value]
        else:
            assert list(cdll_data[value]) == list_data[value]

@pytest.mark.parametrize("index, value, is_error", [
    (slice(2, 10), list(range(8)), False),
    (slice(2, 10, 2), list(range(4)), False),
    (slice(2, None, 3), list(range(3)), False),
    (slice(None, None, -1), list(range(10)), False),
    (slice(-2, -10, -1), list(), ValueError),
    (slice(-2, -10, 'v'), list(), InvalidIntegerSliceError),
    (12, 0, IndexError), 
    (-5, 12, False),
    (slice(None, None, 1), list(), False),
])
def test_setitem(list_data_set, cdll_data_set, index, value, is_error):
    """Test getitem method of CDLL class"""
    if is_error:
        with pytest.raises(is_error):
            cdll_data_set[index] = value

    else:
        list_data_set[index] = value
        cdll_data_set[index] = value
        assert cdll_data_set.size == len(list_data_set)
        assert list(cdll_data_set) == list_data_set

@pytest.mark.parametrize("value, is_error", [
    (slice(2, 4), False),
    (slice(1, None, 6), False),
    (slice(2, 10, 3), False),
    (-5, False),
    (slice(-2, -10, 'v'), InvalidIntegerSliceError),
    (slice(None, None, -1), False),
    (12, IndexError), 
    
])
def test_delitem(list_data_del, cdll_data_del, value, is_error):
    """Test getitem method of CDLL class"""
    if is_error:
        with pytest.raises(is_error):
            print(list(cdll_data_del), value, is_error)
            del cdll_data_del[value]
    else:
        print(list(cdll_data_del), value, is_error)
        del cdll_data_del[value]
        del list_data_del[value]

        assert list(cdll_data_del) == list_data_del

def test_iter(cdll_data):
    """Test cdll method of CDLL class"""
    assert list(cdll_data)== [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    assert cdll_data.size == 10

def test_lshift(cdll_data):
    """Test lshift method of CDLL class"""
    assert cdll_data.head.value == 0
    assert cdll_data.tail.value == 9
    cdll_data << 1
    assert cdll_data.head.value == 9
    assert cdll_data.tail.value == 8

def test_rshift(cdll_data):
    """Test rshift method of CDLL class"""
    assert cdll_data.head.value == 0
    assert cdll_data.tail.value == 9
    cdll_data >> 1
    assert cdll_data.head.value == 1
    assert cdll_data.tail.value == 0

def test_append():
    """Test append method of CDLL class"""
    cdll = CDLList()
    cdll.append(1)
    assert cdll.size == 1
    assert cdll.head.value == 1
    assert cdll.tail.value == 1
    cdll.append(2)
    assert cdll.size == 2
    assert cdll.head.value == 1
    assert cdll.tail.value == 2
    cdll.append(3)
    assert cdll.size == 3
    assert cdll.head.value == 1
    assert cdll.tail.value == 3

def test_appendleft():
    """Test appendleft method of CDLL class"""
    cdll = CDLList()
    cdll.appendleft(1)
    assert cdll.size == 1
    assert cdll.head.value == 1
    assert cdll.tail.value == 1
    cdll.appendleft(2)
    assert cdll.size == 2
    assert cdll.head.value == 2
    assert cdll.tail.value == 1
    cdll.appendleft(3)
    assert cdll.size == 3
    assert cdll.head.value == 3
    assert cdll.tail.value == 1

def test_from_iterable():
    """Test from_iterable method of CDLL class"""
    cdll = CDLList.from_iterable([1, 2, 3])
    assert cdll.size == 3
    assert cdll.head.value == 1
    assert cdll.tail.value == 3