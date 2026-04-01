from pathlib import Path

from .medallion import run_medallion_pipeline


def run_etl() -> dict[str, Path]:
    return run_medallion_pipeline()


if __name__ == "__main__":
    outputs = run_etl()
    print("ETL finished:")
    for layer, path in outputs.items():
        print(f"- {layer}: {path}")
