#!/usr/bin/env python3
"""
Entry point script for Whakarere application.
"""

import sys
print("DEBUG: Starting Whakarere application")
from .application import main

if __name__ == "__main__":
    print("DEBUG: Calling main function")
    result = main()
    print(f"DEBUG: Application finished with result: {result}")
    sys.exit(result)