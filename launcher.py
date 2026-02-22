import sys

if len(sys.argv) == 1:
    sys.argv.insert(1, "--interactive")

import bridge

bridge.main()
