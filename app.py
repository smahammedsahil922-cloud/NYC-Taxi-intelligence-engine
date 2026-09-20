
from pathlib import Path
import sys

import pandas as pd
import streamlit as st
import plotly.express as px


from dashboard.geo_charts import (
    create_borough_demand_chart,
    create_top_pickup_zones_chart,
    create_top_dropoff_zones_chart,
)

# ---------------------------------------------------------
# PROJECT PATH CONFIGURATION
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


# ---------------------------------------------------------
# STREAMLIT PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="NYC Taxi Intelligence Dashboard",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------
# CUSTOM STYLING
# ---------------------------------------------------------

st.markdown(
    """
    <style>
    .main {
        padding-top: 1rem;
    }

    [data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 600;
    }

    .dashboard-subtitle {
        color: #666666;
        font-size: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# DATA PATHS
# ---------------------------------------------------------

CLEANED_DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "yellow_tripdata_2025-01_cleaned.parquet"
)

DAILY_DEMAND_PATH = (
    PROJECT_ROOT / "outputs" / "daily_demand_forecasting.csv"
)

FORECAST_METRICS_PATH = (
    PROJECT_ROOT / "outputs" / "forecast_metrics.csv"
)

FORECAST_PREDICTIONS_PATH = (
    PROJECT_ROOT / "outputs" / "forecast_predictions.csv"
)

HOURLY_DEMAND_PATH = (
    PROJECT_ROOT / "outputs" / "eda_hourly_demand.csv"
)

WEEKDAY_DEMAND_PATH = (
    PROJECT_ROOT / "outputs" / "eda_weekday_demand.csv"
)

PICKUP_ZONE_PATH = (
    PROJECT_ROOT / "outputs" / "eda_pickup_locations.csv"
)

DROPOFF_ZONE_PATH = (
    PROJECT_ROOT / "outputs" / "eda_dropoff_locations.csv"
)

SPATIAL_PICKUP_PATH = (
    PROJECT_ROOT / "outputs" / "spatial_pickup_demand.csv"
)

SPATIAL_DROPOFF_PATH = (
    PROJECT_ROOT / "outputs" / "spatial_dropoff_demand.csv"
)

BOROUGH_DEMAND_PATH = (
    PROJECT_ROOT / "outputs" / "borough_demand.csv"
)


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------


@st.cache_data
def load_cleaned_data():
    if not CLEANED_DATA_PATH.exists():
        return pd.DataFrame()

    # Load only the required columns
    required_columns = [
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "passenger_count",
        "trip_distance",
        "PULocationID",
        "DOLocationID",
        "fare_amount",
        "total_amount",
    ]

    # Read available column names from Parquet metadata
    available_columns = pd.read_parquet(
        CLEANED_DATA_PATH,
        engine="pyarrow",
    ).columns

    selected_columns = [
        column
        for column in required_columns
        if column in available_columns
    ]

    if not selected_columns:
        return pd.DataFrame()

    data = pd.read_parquet(
        CLEANED_DATA_PATH,
        columns=selected_columns,
        engine="pyarrow",
    )

    # Convert datetime columns
    datetime_columns = [
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
    ]

    for column in datetime_columns:
        if column in data.columns:
            data[column] = pd.to_datetime(
                data[column],
                errors="coerce",
            )

    # Create time-based features
    if "tpep_pickup_datetime" in data.columns:
        data["pickup_hour"] = (
            data["tpep_pickup_datetime"].dt.hour
        )

        data["pickup_date"] = (
            data["tpep_pickup_datetime"].dt.date
        )

        data["weekday"] = (
            data["tpep_pickup_datetime"].dt.day_name()
        )

        data["day_type"] = data["weekday"].apply(
            lambda day: (
                "Weekend"
                if day in ["Saturday", "Sunday"]
                else "Weekday"
            )
        )

    return data
   


@st.cache_data
def load_csv(path):
    if not path.exists():
        return pd.DataFrame()

    return pd.read_csv(path)


def format_number(value):
    return f"{value:,.0f}"


def format_currency(value):
    return f"${value:,.2f}"


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

df = load_cleaned_data()

daily_demand = load_csv(DAILY_DEMAND_PATH)
forecast_metrics = load_csv(FORECAST_METRICS_PATH)
forecast_predictions = load_csv(FORECAST_PREDICTIONS_PATH)
hourly_demand = load_csv(HOURLY_DEMAND_PATH)
weekday_demand = load_csv(WEEKDAY_DEMAND_PATH)
pickup_zones = load_csv(PICKUP_ZONE_PATH)
dropoff_zones = load_csv(DROPOFF_ZONE_PATH)

pickup_demand = load_csv(SPATIAL_PICKUP_PATH)
dropoff_demand = load_csv(SPATIAL_DROPOFF_PATH)
borough_demand = load_csv(BOROUGH_DEMAND_PATH)


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

if df.empty:
    st.error(
        "Cleaned dataset not found. Run the cleaning pipeline first."
    )

    st.code(
        "python run_cleaning.py",
        language="powershell",
    )

    st.stop()


# ---------------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------------

st.sidebar.title("Dashboard Filters")

st.sidebar.caption(
    "NYC Taxi Intelligence Engine"
)

if "day_type" in df.columns:
    selected_day_type = st.sidebar.multiselect(
        "Day Type",
        options=sorted(df["day_type"].dropna().unique()),
        default=sorted(df["day_type"].dropna().unique()),
    )

    filtered_df = df[
        df["day_type"].isin(selected_day_type)
    ].copy()
else:
    filtered_df = df.copy()


if "pickup_hour" in filtered_df.columns:
    selected_hours = st.sidebar.slider(
        "Pickup Hour",
        min_value=0,
        max_value=23,
        value=(0, 23),
    )

    filtered_df = filtered_df[
        filtered_df["pickup_hour"].between(
            selected_hours[0],
            selected_hours[1],
        )
    ]


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.title("🚕 NYC Taxi Intelligence Dashboard")

st.markdown(
    """
    <div class="dashboard-subtitle">
    Interactive analytics platform for taxi demand,
    trip behavior, geographic patterns, and forecasting.
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()


# ---------------------------------------------------------
# EXECUTIVE KPIs
# ---------------------------------------------------------

st.subheader("Executive Overview")

total_trips = len(filtered_df)

if "trip_distance" in filtered_df.columns:
    average_distance = filtered_df["trip_distance"].mean()
else:
    average_distance = 0

if "fare_amount" in filtered_df.columns:
    average_fare = filtered_df["fare_amount"].mean()
else:
    average_fare = 0

if "total_amount" in filtered_df.columns:
    total_revenue = filtered_df["total_amount"].sum()
else:
    total_revenue = 0

if "passenger_count" in filtered_df.columns:
    average_passengers = filtered_df["passenger_count"].mean()
else:
    average_passengers = 0


kpi_1, kpi_2, kpi_3, kpi_4, kpi_5 = st.columns(5)

kpi_1.metric(
    "Total Trips",
    format_number(total_trips),
)

kpi_2.metric(
    "Average Distance",
    f"{average_distance:.2f} miles",
)

kpi_3.metric(
    "Average Fare",
    format_currency(average_fare),
)

kpi_4.metric(
    "Total Revenue",
    format_currency(total_revenue),
)

kpi_5.metric(
    "Avg. Passengers",
    f"{average_passengers:.2f}",
)


st.divider()


# ---------------------------------------------------------
# DEMAND ANALYSIS
# ---------------------------------------------------------

st.subheader("Demand Analysis")

demand_col_1, demand_col_2 = st.columns(2)


with demand_col_1:
    st.markdown("#### Hourly Demand")

    if not filtered_df.empty and "pickup_hour" in filtered_df.columns:
        hourly_chart_data = (
            filtered_df.groupby("pickup_hour")
            .size()
            .reset_index(name="trip_count")
        )

        fig_hourly = px.bar(
            hourly_chart_data,
            x="pickup_hour",
            y="trip_count",
            labels={
                "pickup_hour": "Pickup Hour",
                "trip_count": "Number of Trips",
            },
            title="Trips by Pickup Hour",
        )

        fig_hourly.update_layout(
            xaxis=dict(dtick=1),
            hovermode="x unified",
        )

        st.plotly_chart(
            fig_hourly,
            use_container_width=True,
        )
    else:
        st.info("Hourly demand data unavailable.")


with demand_col_2:
    st.markdown("#### Day Type Demand")

    if not filtered_df.empty and "day_type" in filtered_df.columns:
        day_type_data = (
            filtered_df.groupby("day_type")
            .size()
            .reset_index(name="trip_count")
        )

        fig_day_type = px.pie(
            day_type_data,
            names="day_type",
            values="trip_count",
            title="Weekday versus Weekend Trips",
        )

        st.plotly_chart(
            fig_day_type,
            use_container_width=True,
        )
    else:
        st.info("Day type data unavailable.")


# ---------------------------------------------------------
# DAILY DEMAND TREND
# ---------------------------------------------------------

st.subheader("Daily Demand Trend")

if not filtered_df.empty and "pickup_date" in filtered_df.columns:
    daily_chart_data = (
        filtered_df.groupby("pickup_date")
        .size()
        .reset_index(name="trip_count")
    )

    daily_chart_data["pickup_date"] = pd.to_datetime(
        daily_chart_data["pickup_date"]
    )

    fig_daily = px.line(
        daily_chart_data,
        x="pickup_date",
        y="trip_count",
        markers=True,
        title="Daily Taxi Trip Volume",
        labels={
            "pickup_date": "Date",
            "trip_count": "Trips",
        },
    )

    st.plotly_chart(
        fig_daily,
        use_container_width=True,
    )
else:
    st.info("Daily demand data unavailable.")


st.divider()


# ---------------------------------------------------------
# ZONE ANALYSIS
# ---------------------------------------------------------

st.subheader("Pickup and Drop-off Zone Analysis")

zone_col_1, zone_col_2 = st.columns(2)


with zone_col_1:
    st.markdown("#### Top Pickup Zones")

    if not filtered_df.empty and "PULocationID" in filtered_df.columns:
        top_pickup = (
            filtered_df["PULocationID"]
            .value_counts()
            .head(15)
            .reset_index()
        )

        top_pickup.columns = [
            "zone_id",
            "trip_count",
        ]

        fig_pickup = px.bar(
            top_pickup.sort_values("trip_count"),
            x="trip_count",
            y="zone_id",
            orientation="h",
            title="Top 15 Pickup Locations",
            labels={
                "zone_id": "Pickup Zone ID",
                "trip_count": "Trips",
            },
        )

        st.plotly_chart(
            fig_pickup,
            use_container_width=True,
        )
    else:
        st.info("Pickup zone data unavailable.")


with zone_col_2:
    st.markdown("#### Top Drop-off Zones")

    if not filtered_df.empty and "DOLocationID" in filtered_df.columns:
        top_dropoff = (
            filtered_df["DOLocationID"]
            .value_counts()
            .head(15)
            .reset_index()
        )

        top_dropoff.columns = [
            "zone_id",
            "trip_count",
        ]

        fig_dropoff = px.bar(
            top_dropoff.sort_values("trip_count"),
            x="trip_count",
            y="zone_id",
            orientation="h",
            title="Top 15 Drop-off Locations",
            labels={
                "zone_id": "Drop-off Zone ID",
                "trip_count": "Trips",
            },
        )

        st.plotly_chart(
            fig_dropoff,
            use_container_width=True,
        )
    else:
        st.info("Drop-off zone data unavailable.")


st.divider()


# ---------------------------------------------------------
# FARE AND DISTANCE ANALYSIS
# ---------------------------------------------------------

st.subheader("Fare and Trip Distance Analysis")

fare_col_1, fare_col_2 = st.columns(2)


with fare_col_1:
    if (
        not filtered_df.empty
        and "trip_distance" in filtered_df.columns
        and "fare_amount" in filtered_df.columns
    ):
        fig_scatter = px.scatter(
            filtered_df.sample(
                min(len(filtered_df), 5000),
                random_state=42,
            ),
            x="trip_distance",
            y="fare_amount",
            opacity=0.5,
            title="Trip Distance versus Fare",
            labels={
                "trip_distance": "Trip Distance (miles)",
                "fare_amount": "Fare Amount ($)",
            },
        )

        st.plotly_chart(
            fig_scatter,
            use_container_width=True,
        )


with fare_col_2:
    if (
        not filtered_df.empty
        and "fare_amount" in filtered_df.columns
    ):
        fig_fare = px.histogram(
            filtered_df,
            x="fare_amount",
            nbins=50,
            title="Fare Distribution",
            labels={
                "fare_amount": "Fare Amount ($)",
            },
        )

        st.plotly_chart(
            fig_fare,
            use_container_width=True,
        )


st.divider()


# ---------------------------------------------------------
# FORECASTING ANALYSIS
# ---------------------------------------------------------

st.subheader("Demand Forecasting")

forecast_col_1, forecast_col_2 = st.columns(2)


with forecast_col_1:
    st.markdown("#### Forecast Model Performance")

    if not forecast_metrics.empty:
        st.dataframe(
            forecast_metrics,
            use_container_width=True,
            hide_index=True,
        )

        numeric_metric_columns = [
            column
            for column in ["MAE", "RMSE"]
            if column in forecast_metrics.columns
        ]

        if numeric_metric_columns and "model" in forecast_metrics.columns:
            metric_chart = forecast_metrics[
                ["model"] + numeric_metric_columns
            ].melt(
                id_vars="model",
                var_name="metric",
                value_name="value",
            )

            fig_metrics = px.bar(
                metric_chart,
                x="model",
                y="value",
                color="metric",
                barmode="group",
                title="Forecasting Model Comparison",
            )

            st.plotly_chart(
                fig_metrics,
                use_container_width=True,
            )
    else:
        st.info(
            "Forecast metrics unavailable. Run Phase 8 forecasting."
        )


with forecast_col_2:
    st.markdown("#### Daily Forecast Predictions")

    if not forecast_predictions.empty:
        date_column = None

        for possible_column in [
            "date",
            "tpep_pickup_datetime",
            "pickup_date",
        ]:
            if possible_column in forecast_predictions.columns:
                date_column = possible_column
                break

        if date_column and "trip_count" in forecast_predictions.columns:
            forecast_predictions[date_column] = pd.to_datetime(
                forecast_predictions[date_column],
                errors="coerce",
            )

            prediction_columns = [
                column
                for column in [
                    "trip_count",
                    "naive_prediction",
                    "moving_average_prediction",
                    "seasonal_naive_prediction",
                ]
                if column in forecast_predictions.columns
            ]

            if len(prediction_columns) > 1:
                forecast_chart_data = forecast_predictions[
                    [date_column] + prediction_columns
                ].melt(
                    id_vars=date_column,
                    var_name="series",
                    value_name="trips",
                )

                fig_forecast = px.line(
                    forecast_chart_data,
                    x=date_column,
                    y="trips",
                    color="series",
                    title="Actual versus Baseline Predictions",
                )

                st.plotly_chart(
                    fig_forecast,
                    use_container_width=True,
                )
        else:
            st.dataframe(
                forecast_predictions,
                use_container_width=True,
            )
    else:
        st.info(
            "Forecast predictions unavailable. Run Phase 8 forecasting."
        )


st.divider()


# ---------------------------------------------------------
# ADVANCED GEOGRAPHIC ANALYTICS
# ---------------------------------------------------------

st.header("Advanced Geographic Analytics")

if (
    not pickup_demand.empty
    and not dropoff_demand.empty
    and not borough_demand.empty
):
    st.subheader("Pickup Demand by Borough")
    st.plotly_chart(
        create_borough_demand_chart(borough_demand),
        use_container_width=True,
    )

    geo_col_1, geo_col_2 = st.columns(2)

    with geo_col_1:
        st.subheader("Top Pickup Zones")
        st.plotly_chart(
            create_top_pickup_zones_chart(pickup_demand),
            use_container_width=True,
        )

    with geo_col_2:
        st.subheader("Top Drop-off Zones")
        st.plotly_chart(
            create_top_dropoff_zones_chart(dropoff_demand),
            use_container_width=True,
        )

    st.subheader("Top Pickup Zones Table")
    st.dataframe(
        pickup_demand.head(20),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.warning(
        "Geographic reports unavailable. Run: python run_geospatial.py"
    )


st.divider()


# ---------------------------------------------------------
# DATA EXPLORER
# ---------------------------------------------------------

st.subheader("Filtered Data Explorer")

st.caption(
    f"Displaying {format_number(len(filtered_df))} filtered records."
)

st.dataframe(
    filtered_df.head(1000),
    use_container_width=True,
    hide_index=True,
)

csv_data = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Filtered Data as CSV",
    data=csv_data,
    file_name="filtered_taxi_data.csv",
    mime="text/csv",
)


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.divider()

st.caption(
    "Built with Python, Pandas, Plotly, and Streamlit | "
    "NYC Taxi Intelligence Engine"
)



