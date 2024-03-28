"""A printer for human-readable output of types and variables."""

from pytype import pretty_printer_base
from pytype.pytd import pytd_utils
from pytype.rewrite.flow import variables
from pytype.types import types


class PrettyPrinter(pretty_printer_base.PrettyPrinterBase):
  """Pretty print types for errors."""

  def print_as_generic_type(self, t) -> str:
    return repr(t)

  def print_as_expected_type(self, t: types.BaseValue, instance=None) -> str:
    """Print abstract value t as a pytd type."""
    return self.print_pytd(t.to_pytd_type_of_instance())

  def print_as_actual_type(self, t, literal=False) -> str:
    return repr(t)

  def print_as_function_def(self, fn: types.Function) -> str:
    return repr(fn)

  def print_var_as_type(self, var: variables.Variable, node) -> str:
    """Print a pytype variable as a type."""
    del node  # not used in rewrite
    typ = pytd_utils.JoinTypes(v.to_pytd_type() for v in var.values)
    return self.print_pytd(typ)

  def show_variable(self, var: variables.Variable) -> str:
    """Show variable as 'name: typ' or 'pyval: typ' if available."""
    return repr(var)
