from __future__ import annotations

from src.web_app import create_app, run_local

app = create_app(serve_local_static=True)


if __name__ == "__main__":
    run_local()
