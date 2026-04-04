from __future__ import annotations

import os

from src.web_app import create_app, run_local, truthy

# Vercel exposes a VERCEL env var in the runtime; locally we keep static serving enabled.
app = create_app(serve_local_static=not truthy(os.getenv("VERCEL")))


if __name__ == "__main__":
    run_local()
