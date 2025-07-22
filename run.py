#!/usr/bin/env python3
"""
Entry point script for the GovDocVerify.
This script provides a simple way to run the application from the command line.
"""

import sys

from backend.cli import main

if __name__ == "__main__":
    sys.exit(main())
