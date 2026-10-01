"""Cross-check our text snapshots against independent witnesses (needs the network).

uv run python scripts/crosscheck.py [--script uthmani ...]
"""

import sys

from quranjson.crosscheck import main

if __name__ == "__main__":
    sys.exit(main())
