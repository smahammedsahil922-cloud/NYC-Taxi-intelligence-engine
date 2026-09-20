from taxi_intelligence.config import (
    PROJECT_NAME,
    PROJECT_VERSION,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    OUTPUT_DIR,
)


def main() -> None:
    print("=" * 60)
    print(PROJECT_NAME)
    print("=" * 60)
    print(f"Version: {PROJECT_VERSION}")
    print(f"Raw data directory: {RAW_DATA_DIR}")
    print(f"Processed data directory: {PROCESSED_DATA_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    print("Phase 1 project setup is working successfully!")


if __name__ == "__main__":
    main()