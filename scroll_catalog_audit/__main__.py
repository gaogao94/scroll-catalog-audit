"""Entry point for ``python -m scroll_catalog_audit <subcommand>``.

The README documents this form and CI uses ``python -m scroll_catalog_audit.audit``; without this file
the documented form fails with "No module named scroll_catalog_audit.__main__", which a fresh clone
hits on its first command. Both forms now run the same CLI.
"""

from __future__ import annotations

import sys

from scroll_catalog_audit.audit import main

if __name__ == "__main__":
    sys.exit(main())
