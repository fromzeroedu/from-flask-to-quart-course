"""
ASGI file for Hypercorn
"""

import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from my_app.application import create_app

app = asyncio.run(create_app())

if __name__ == "__main__":
    app.run()
