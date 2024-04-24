"""Abstract-representation-independent base class for pretty printing."""

import abc
import re
from typing import Iterable

from pytype.pytd import escape
from pytype.pytd import optimize
from pytype.pytd import pytd
from pytype.pytd import pytd_utils
from pytype.pytd import visitors
from pytype.types import types


class PrettyPrinterBase(abc.ABC):
  """Pretty printer methods depending only on pytd types.

  Subclasses are expected to handle abstract->pytd conversion.
  """

  def __init__(self, ctx):
    self.ctx = ctx

  @staticmethod
  def show_constant(val: types.BaseValue) -> str:
    """Pretty-print a value if it is a constant.

    Recurses into a constant, printing the underlying Python value for constants
    and just using "..." for everything else (e.g., Variables). This is useful
    for generating clear error messages that show the exact values related to an
    error while preventing implementation details from leaking into the message.

    Args:
      val: an abstract value.

    Returns:
      A string of the pretty-printed constant.
    """
    def _ellipsis_printer(v):
      if isinstance(v, types.PythonConstant):
        return v.str_of_constant(_ellipsis_printer)
      return "..."
    return _ellipsis_printer(val)

  def print_pytd(self, pytd_type: pytd.Type) -> str:
    """Print the name of the pytd type."""
    typ = pytd_utils.CanonicalOrdering(
        optimize.Optimize(
            pytd_type.Visit(visitors.RemoveUnknownClasses())))
    name = pytd_utils.Print(typ)
    # Clean up autogenerated namedtuple names, e.g. "namedtuple-X-a-_0-c"
    # becomes just "X", by extracting out just the type name.
    if "namedtuple" in name:
      return escape.unpack_namedtuple(name)
    nested_class_match = re.search(r"_(?:\w+)_DOT_", name)
    if nested_class_match:
      # Pytype doesn't have true support for nested classes. Instead, for
      #   class Foo:
      #     class Bar: ...
      # it outputs:
      #   class _Foo_DOT_Bar: ...
      #   class Foo:
      #     Bar = ...  # type: Type[_Foo_DOT_Bar]
      # Replace _Foo_DOT_Bar with Foo.Bar in error messages for readability.
      # TODO(b/35138984): Get rid of this hack.
      start = nested_class_match.start()
      return name[:start] + name[start+1:].replace("_DOT_", ".")
    return name

  def join_printed_types(self, typs: Iterable[str]) -> str:
    """Pretty-print the union of the printed types."""
    typs = set(typs)  # dedup
    if len(typs) == 1:
      return next(iter(typs))
    elif typs:
      literal_contents = set()
      optional = False
      new_types = []
      for t in typs:
        if t.startswith("Literal["):
          literal_contents.update(t[len("Literal["):-1].split(", "))
        elif t == "None":
          optional = True
        else:
          new_types.append(t)
      if literal_contents:
        literal = f"Literal[{', '.join(sorted(literal_contents))}]"
        new_types.append(literal)
      if len(new_types) > 1:
        out = f"Union[{', '.join(sorted(new_types))}]"
      else:
        out = new_types[0]
      if optional:
        out = f"Optional[{out}]"
      return out
    else:
      # TODO(mdemello): change this to Never
      return "nothing"

  @abc.abstractmethod
  def print_generic_type(self, t: types.BaseValue) -> str:
    """Returns a string of the generic type of t.

    For example, if t is `[0]`, then this method returns "list[int]".

    Args:
      t: An abstract value.
    """

  @abc.abstractmethod
  def print_type_of_instance(self, t: types.BaseValue, instance=None) -> str:
    """Returns a string of the type of an instance of t.

    For example, if t is `int`, then this method returns "int".

    Args:
      t: An abstract value.
      instance: A specific instance of t to print.
    """

  @abc.abstractmethod
  def print_type(self, t, literal=False) -> str:
    """Returns a string of the type of t.

    For example, if t is `0`, then this method returns "int" with literal=False
    or `Literal[0]` with literal=True.

    Args:
      t: An abstract value.
      literal: Whether to print literals literally.
    """

  @abc.abstractmethod
  def print_function_def(self, fn: types.Function) -> str:
    """Print a function definition."""

  @abc.abstractmethod
  def print_var_type(self, var: types.Variable, *args) -> str:
    """Print a pytype variable as a type."""

  @abc.abstractmethod
  def show_variable(self, var: types.Variable) -> str:
    """Show variable as 'name: typ' or 'pyval: typ' if available."""