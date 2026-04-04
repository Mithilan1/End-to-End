from __future__ import annotations

from src.web_app import create_app

app = create_app(serve_local_static=False)
