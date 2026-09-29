"""Built-in detection rules, grouped per language family."""

from .java_rules import JAVA_RULES
from .javascript_rules import JAVASCRIPT_RULES
from .python_rules import PYTHON_RULES

__all__ = ["PYTHON_RULES", "JAVASCRIPT_RULES", "JAVA_RULES"]
