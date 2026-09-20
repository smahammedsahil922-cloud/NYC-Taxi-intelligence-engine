from __future__ import annotations

import pandas as pd
import plotly.express as px


def create_borough_demand_chart(
    borough_demand: pd.DataFrame,
):
    """Create a borough-level demand chart."""
    return px.bar(
        borough_demand,
        x="pickup_borough",
        y="trip_count",
        title="Taxi Demand by Pickup Borough",
        labels={
            "pickup_borough": "Borough",
            "trip_count": "Trips",
        },
    )


def create_top_pickup_zones_chart(
    pickup_demand: pd.DataFrame,
    top_n: int = 15,
):
    """Create a top pickup zones chart."""
    chart_data = pickup_demand.head(top_n).copy()

    chart_data["zone_label"] = (
        chart_data["pickup_zone"].fillna("Unknown")
        + " — "
        + chart_data["pickup_borough"].fillna("Unknown")
    )

    return px.bar(
        chart_data.sort_values("pickup_trip_count"),
        x="pickup_trip_count",
        y="zone_label",
        orientation="h",
        title=f"Top {top_n} Pickup Zones",
        labels={
            "pickup_trip_count": "Trips",
            "zone_label": "Taxi Zone",
        },
    )


def create_top_dropoff_zones_chart(
    dropoff_demand: pd.DataFrame,
    top_n: int = 15,
):
    """Create a top drop-off zones chart."""
    chart_data = dropoff_demand.head(top_n).copy()

    chart_data["zone_label"] = (
        chart_data["dropoff_zone"].fillna("Unknown")
        + " — "
        + chart_data["dropoff_borough"].fillna("Unknown")
    )

    return px.bar(
        chart_data.sort_values("dropoff_trip_count"),
        x="dropoff_trip_count",
        y="zone_label",
        orientation="h",
        title=f"Top {top_n} Drop-off Zones",
        labels={
            "dropoff_trip_count": "Trips",
            "zone_label": "Taxi Zone",
        },
    )


def create_pickup_dropoff_flow(
    enriched_data: pd.DataFrame,
    top_n: int = 20,
):
    """Create a pickup-to-drop-off flow table."""
    flow = (
        enriched_data.groupby(
            [
                "pickup_zone",
                "dropoff_zone",
            ],
            dropna=False,
        )
        .size()
        .reset_index(name="trip_count")
        .sort_values("trip_count", ascending=False)
        .head(top_n)
    )

    return flow