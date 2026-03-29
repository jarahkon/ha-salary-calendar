"""Pytest configuration.

Adds the salary subpackage to the path so tests can import it
without triggering the HA-dependent parent package __init__.py.

The path is appended (not prepended) so that the stdlib ``calendar``
module is found before the HA ``calendar.py`` entity file that lives
in the same directory.
"""

import calendar as _calendar  # noqa: F401  -- pre-load stdlib calendar
import sys
from pathlib import Path

# Append so stdlib modules keep priority over same-named HA files
_salary_pkg = Path(__file__).parent.parent / "custom_components" / "salary_calendar"
sys.path.append(str(_salary_pkg))
