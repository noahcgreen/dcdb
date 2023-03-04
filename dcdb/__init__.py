import logging

import sys

# FIXME: Prevents recursion error (see test_long_game)
sys.setrecursionlimit(3000)

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
