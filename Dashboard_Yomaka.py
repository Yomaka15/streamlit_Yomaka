import pandas as pd
import streamlit as st
import plotly.express as px
from babel.numbers import format_currency

# =========================
# FUNCTIONS
# =========================
def create_daily_orders_df(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.resample("D", on="order_date")
        .agg(
            order_count=("order_id", "nunique"),
            revenue=("total_price", "sum"),
        )
        .reset_index()
    )


def create_sum_order_items_df(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    qty_col = "quantity_x" if "quantity_x" in df.columns else "quantity"
    out = (
        df.groupby("product_name", as_index=False)[qty_col]
        .sum()
        .sort_values(qty_col, ascending=False)
    )
    return out, qty_col


def create_bygender_df(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("gender", as_index=False)["customer_id"]
        .nunique()
        .rename(columns={"customer_id": "customer_count"})
    )


def create_byage_df(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("age_group", as_index=False)["customer_id"]
        .nunique()
        .rename(columns={"customer_id": "customer_count"})
    )


def create_bystate_df(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("state", as_index=False)["customer_id"]
        .nunique()
        .rename(columns={"customer_id": "customer_count"})
        .sort_values("customer_count", ascending=False)
    )


def create_rfm_df(df: pd.DataFrame) -> pd.DataFrame:
    # Pastikan datetime
    df = df.copy()
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")

    rfm = df.groupby("customer_id", as_index=False).agg(
        last_order=("order_date", "max"),
        frequency=("order_id", "nunique"),
        monetary=("total_price", "sum"),
    )

    # FIX: jangan pakai .dt.date (bikin tipe jadi date biasa)
    recent_date = df["order_date"].max()
    rfm["last_order"] = pd.to_datetime(rfm["last_order"], errors="coerce")
    rfm["recency"] = (recent_date - rfm["last_order"]).dt.days

    return rfm.drop(columns=["last_order"])


def money_aud(x: float) -> str:
    return format_currency(x, "AUD", locale="es_CO")


# =========================
# APP CONFIG
# =========================
st.set_page_config(page_title="My Collection Dashboard", layout="wide")

# =========================
# LOAD DATA
# =========================
df = pd.read_csv("all_data.csv")

# Pastikan kolom tanggal jadi datetime (aman walau ada nilai aneh)
for col in ["order_date", "delivery_date"]:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")

# Buang baris yang order_date kosong biar resample & filter aman
df = df.dropna(subset=["order_date"]).sort_values("order_date")

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.image(
        "https://raw.githubusercontent.com/mhvvn/dashboard_streamlit/refs/heads/main/img/tshirt.png",
        width=80,
    )

    min_d = df["order_date"].min().date()
    max_d = df["order_date"].max().date()

    start_date, end_date = st.date_input(
        "Rentang Waktu",
        value=[min_d, max_d],
        min_value=min_d,
        max_value=max_d,
    )

# Filter data (inclusive)
start_ts = pd.to_datetime(start_date)
end_ts = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

df = df[(df["order_date"] >= start_ts) & (df["order_date"] <= end_ts)].copy()

if df.empty:
    st.warning("Data kosong untuk rentang waktu yang dipilih. Coba pilih rentang lain.")
    st.stop()

# =========================
# PREP DATAFRAMES
# =========================
daily_orders = create_daily_orders_df(df)
products, qty_col = create_sum_order_items_df(df)

gender_df = create_bygender_df(df) if "gender" in df.columns else pd.DataFrame(columns=["gender", "customer_count"])
age_df = create_byage_df(df) if "age_group" in df.columns else pd.DataFrame(columns=["age_group", "customer_count"])
state_df = create_bystate_df(df) if "state" in df.columns else pd.DataFrame(columns=["state", "customer_count"])

rfm_df = create_rfm_df(df)

# =========================
# DASHBOARD
# =========================
st.header("My Collection Dashboard ✨")

# ---- METRICS ----
c1, c2 = st.columns(2)
c1.metric("Total Orders", int(daily_orders["order_count"].sum()))
c2.metric("Total Revenue", money_aud(float(daily_orders["revenue"].sum())))

# ---- DAILY ORDERS ----
st.subheader("Daily Orders")
fig = px.line(
    daily_orders,
    x="order_date",
    y="order_count",
    markers=True,
    title="Daily Orders Trend",
)
st.plotly_chart(fig, use_container_width=True)

# ---- BEST & WORST PRODUCT ----
st.subheader("Best & Worst Performing Product")

best = products.head(5)
worst = products.tail(5)

c1, c2 = st.columns(2)

c1.plotly_chart(
    px.bar(
        best,
        x=qty_col,
        y="product_name",
        orientation="h",
        title="Best Product",
    ).update_layout(yaxis=dict(autorange="reversed")),
    use_container_width=True,
)

c2.plotly_chart(
    px.bar(
        worst,
        x=qty_col,
        y="product_name",
        orientation="h",
        title="Worst Product",
    ).update_layout(yaxis=dict(autorange="reversed"), xaxis_autorange="reversed"),
    use_container_width=True,
)

# ---- CUSTOMER DEMOGRAPHICS ----
st.subheader("Customer Demographics")

c1, c2 = st.columns(2)

c1.plotly_chart(
    px.bar(gender_df, x="gender", y="customer_count", title="Customer by Gender"),
    use_container_width=True,
)

c2.plotly_chart(
    px.bar(age_df, x="age_group", y="customer_count", title="Customer by Age"),
    use_container_width=True,
)

st.plotly_chart(
    px.bar(
        state_df.head(10),
        x="customer_count",
        y="state",
        orientation="h",
        title="Customer by State (Top 10)",
    ).update_layout(yaxis=dict(autorange="reversed")),
    use_container_width=True,
)

# ---- RFM ----
st.subheader("Best Customer Based on RFM")

c1, c2, c3 = st.columns(3)
c1.metric("Avg Recency", round(float(rfm_df["recency"].mean()), 1))
c2.metric("Avg Frequency", round(float(rfm_df["frequency"].mean()), 2))
c3.metric("Avg Monetary", money_aud(float(rfm_df["monetary"].mean())))

c1, c2, c3 = st.columns(3)

c1.plotly_chart(
    px.bar(
        rfm_df.sort_values("recency").head(5),
        x="recency",
        y="customer_id",
        orientation="h",
        title="Top Recency",
    ).update_layout(yaxis=dict(autorange="reversed")),
    use_container_width=True,
)

c2.plotly_chart(
    px.bar(
        rfm_df.sort_values("frequency", ascending=False).head(5),
        x="frequency",
        y="customer_id",
        orientation="h",
        title="Top Frequency",
    ).update_layout(yaxis=dict(autorange="reversed")),
    use_container_width=True,
)

c3.plotly_chart(
    px.bar(
        rfm_df.sort_values("monetary", ascending=False).head(5),
        x="monetary",
        y="customer_id",
        orientation="h",
        title="Top Monetary",
    ).update_layout(yaxis=dict(autorange="reversed")),
    use_container_width=True,
)

st.caption("© My Collection 2025")
