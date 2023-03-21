"""Tests for the fiddle overlay."""

from pytype.tests import test_base


_FIDDLE_PYI = """
from typing import Callable, Generic, Type, TypeVar, Union

T = TypeVar("T")

class Buildable(Generic[T], metaclass=abc.ABCMeta):
  def __init__(self, fn_or_cls: Union[Buildable, Type[T], Callable[..., T]], *args, **kwargs) -> None:
    self = Buildable[T]

class Config(Generic[T], Buildable[T]):
  ...
"""


class TestDataclassConfig(test_base.BaseTest):
  """Tests for Config wrapping a dataclass."""

  def test_basic(self):
    with self.DepTree([("fiddle.pyi", _FIDDLE_PYI)]):
      self.CheckWithErrors("""
        import dataclasses
        import fiddle

        @dataclasses.dataclass
        class Simple:
          x: int
          y: str

        a = fiddle.Config(Simple)
        a.x = 1
        a.y = 2  # annotation-type-mismatch
      """)

  def test_return_type(self):
    with self.DepTree([("fiddle.pyi", _FIDDLE_PYI)]):
      self.Check("""
        import dataclasses
        import fiddle

        @dataclasses.dataclass
        class Simple:
          x: int
          y: str

        def f() -> fiddle.Config[Simple]:
          a = fiddle.Config(Simple)
          a.x = 1
          return a
      """)

  def test_pyi(self):
    with self.DepTree([
        ("fiddle.pyi", _FIDDLE_PYI),
        ("foo.pyi", """
            import dataclasses
            import fiddle

            @dataclasses.dataclass
            class Simple:
              x: int
              y: str

            a: fiddle.Config[Simple]
         """)]):
      self.CheckWithErrors("""
        import foo
        a = foo.a
        a.x = 1
        a.y = 2  # annotation-type-mismatch
      """)

  def test_nested_dataclasses(self):
    with self.DepTree([("fiddle.pyi", _FIDDLE_PYI)]):
      self.CheckWithErrors("""
        import dataclasses
        import fiddle

        @dataclasses.dataclass
        class Simple:
          x: int
          y: str

        @dataclasses.dataclass
        class Complex:
          x: Simple
          y: str

        a = fiddle.Config(Complex)
        a.x.x = 1
        a.x.y = 2  # annotation-type-mismatch
      """)

  def test_frozen_dataclasses(self):
    with self.DepTree([("fiddle.pyi", _FIDDLE_PYI)]):
      self.CheckWithErrors("""
        import dataclasses
        import fiddle

        @dataclasses.dataclass(frozen=True)
        class Simple:
          x: int
          y: str

        @dataclasses.dataclass(frozen=True)
        class Complex:
          x: Simple
          y: str

        a = fiddle.Config(Complex)
        a.x.x = 1
        a.x.y = 2  # annotation-type-mismatch
      """)

  def test_non_dataclass(self):
    # Config values wrapping non-dataclasses are currently treated as Any
    with self.DepTree([("fiddle.pyi", _FIDDLE_PYI)]):
      self.Check("""
        import fiddle

        class Simple:
          x: int
          y: str

        a = fiddle.Config(Simple)
        a.x = 1
        a.y = 2
      """)

  def test_init_args(self):
    with self.DepTree([("fiddle.pyi", _FIDDLE_PYI)]):
      self.CheckWithErrors("""
        import dataclasses
        import fiddle

        @dataclasses.dataclass
        class Simple:
          x: int
          y: str

        a = fiddle.Config(Simple, x=1, y='2')
        b = fiddle.Config(Simple, 1, '2')
        c = fiddle.Config(Simple, 1, y='2')
        d = fiddle.Config(Simple, x='a', y='2')  # wrong-arg-types
        e = fiddle.Config(Simple, x=1)  # partial initialization is fine
        f = fiddle.Config(Simple, x=1, y='2', z=3)  # wrong-keyword-args
        g = fiddle.Config(Simple, 1, 2, 3)  # wrong-arg-count
      """)


if __name__ == "__main__":
  test_base.main()