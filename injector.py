import builtins
import os
import runpy

original_input = builtins.input
builtins.input = lambda prompt='': os.getenv("SORT_MODE", "2")  # default to ROI ascending

import sys
runpy.run_path(sys.argv[1], run_name="__main__")
