from __future__ import annotations

from pathlib import Path
import json

import geopandas as gpd
import pandas as pd
import plotly.express as px


def load_taxi_zone_boundaries(
    boundary_path: str | Path,
) -> gpd.GeoDataFrame:
    """Load NYC taxi-zone boundaries."""
    path = Path(boundary_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Boundary file not found: {path}"
        )

    if path.suffix.lower() == ".zip":
        source = f"zip://{path.resolve()}"
    else:
        source = str(path)

    zones = gpd.read_file(source)

    if "LocationID" not in zones.columns:
        raise ValueError(
            "Boundary file must contain LocationID."
        )

    zones["LocationID"] = pd.to_numeric(
        zones["LocationID"],
        errors="coerce",
    )

    zones = zones.dropna(
        subset=["LocationID"]
    ).copy()

    zones["LocationID"] = zones["LocationID"].astype(int)

    # GeoJSON coordinates are commonly represented in WGS84.
    if zones.crs is not None:
        zones = zones.to_crs(epsg=4326)

    return zones


def create_pickup_demand_geojson(
    boundaries: gpd.GeoDataFrame,
    pickup_demand: pd.DataFrame,
) -> dict:
    """Join pickup demand to taxi-zone boundaries."""
    demand = pickup_demand.copy()

    demand["PULocationID"] = pd.to_numeric(
        demand["PULocationID"],
        errors="coerce",
    )

    demand = demand.rename(
        columns={
            "PULocationID": "LocationID",
        }
    )

    demand = demand[
        ["LocationID", "pickup_trip_count"]
    ]

    merged = boundaries.merge(
        demand,
        on="LocationID",
        how="left",
    )

    merged["pickup_trip_count"] = (
        merged["pickup_trip_count"]
        .fillna(0)
    )

    return json.loads(
        merged.to_json()
    )


def create_pickup_choropleth(
    geojson_data: dict,
):
    """Create an interactive pickup-demand choropleth."""
    features = geojson_data.get("features", [])

    map_data = []

    for feature in features:
        properties = feature.get("properties", {})

        map_data.append(
            {
                "LocationID": properties.get(
                    "LocationID"
                ),
                "pickup_trip_count": properties.get(
                    "pickup_trip_count",
                    0,
                ),
            }
        )

    map_df = pd.DataFrame(map_data)

    return px.choropleth(
        map_df,
        geojson=geojson_data,
        locations="LocationID",
        featureidkey="properties.LocationID",
        color="pickup_trip_count",
        color_continuous_scale="Viridis",
        scope="usa",
        title="NYC Pickup Demand by Taxi Zone",
        labels={
            "pickup_trip_count": "Pickup Trips",
        },
    )