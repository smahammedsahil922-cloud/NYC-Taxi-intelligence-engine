from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent

sys.path.insert(
    0,
    str(PROJECT_ROOT / "src"),
)

from taxi_intelligence.geospatial.zone_lookup import (
    load_zone_lookup,
    enrich_trip_locations,
    generate_spatial_demand_report,
)


CLEANED_DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "yellow_tripdata_2025-01_cleaned.parquet"
)

ZONE_LOOKUP_PATH = (
    PROJECT_ROOT
    / "data"
    / "reference"
    / "taxi_zone_lookup.csv"
)

OUTPUTS_PATH = PROJECT_ROOT / "outputs"

ENRICHED_DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "yellow_tripdata_2025-01_geospatial.parquet"
)


def main() -> None:
    if not CLEANED_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Cleaned dataset not found: {CLEANED_DATA_PATH}"
        )

    zones = load_zone_lookup(ZONE_LOOKUP_PATH)
    trips = pd.read_parquet(CLEANED_DATA_PATH)

    enriched_data = enrich_trip_locations(
        trips=trips,
        zones=zones,
    )

    (
        pickup_demand,
        dropoff_demand,
        borough_demand,
    ) = generate_spatial_demand_report(enriched_data)

    OUTPUTS_PATH.mkdir(parents=True, exist_ok=True)

    enriched_data.to_parquet(
        ENRICHED_DATA_PATH,
        index=False,
    )

    pickup_demand.to_csv(
        OUTPUTS_PATH / "spatial_pickup_demand.csv",
        index=False,
    )

    dropoff_demand.to_csv(
        OUTPUTS_PATH / "spatial_dropoff_demand.csv",
        index=False,
    )

    borough_demand.to_csv(
        OUTPUTS_PATH / "borough_demand.csv",
        index=False,
    )

    print("\nGeospatial analysis completed.")
    print(f"Trips processed: {len(enriched_data):,}")
    print(f"Zone records: {len(zones):,}")

    print("\nTop pickup zones:")
    print(pickup_demand.head(10).to_string(index=False))

    print("\nBorough demand:")
    print(borough_demand.to_string(index=False))

    print("\nOutput files created:")
    print(ENRICHED_DATA_PATH)
    print(OUTPUTS_PATH / "spatial_pickup_demand.csv")
    print(OUTPUTS_PATH / "spatial_dropoff_demand.csv")
    print(OUTPUTS_PATH / "borough_demand.csv")


if __name__ == "__main__":
    main()