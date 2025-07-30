import hypothesis.strategies as st
from hypothesis import given


@given(st.integers(), st.integers())
def test_addition_commutative(a, b):
    assert a + b == b + a
