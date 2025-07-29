import hypothesis.strategies as st
from hypothesis import given


@given(st.integers(), st.integers())
def test_addition_commutative(a, b):
    print(f"TEST\na: {a}, b: {b}, a+b: {a + b}")
    assert a + b == b + a
