from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(page_title="購買ダッシュボード", page_icon="📊", layout="wide")

CSV_PATH = Path(__file__).parent / "date" / "sample-data.csv"
REQUIRED_COLUMNS = [
    "顧客ID",
    "年齢",
    "性別",
    "地域",
    "購入カテゴリー",
    "購入金額",
    "購入日",
    "支払方法",
]


@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8")
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"必須列が不足しています: {', '.join(missing)}")

    df["購入日"] = pd.to_datetime(df["購入日"], errors="coerce")
    df["購入金額"] = pd.to_numeric(df["購入金額"], errors="coerce")
    df = df.dropna(subset=["購入日", "購入金額"])
    df["年月"] = df["購入日"].dt.to_period("M").astype(str)
    return df


def format_yen(value: float) -> str:
    return f"¥{value:,.0f}"


st.title("購買ダッシュボード（M1）")
st.caption("M1: 基本KPI・基本3グラフ・基本フィルタ")

if not CSV_PATH.exists():
    st.error(f"データファイルが見つかりません: {CSV_PATH}")
    st.stop()

try:
    data = load_data(CSV_PATH)
except Exception as exc:
    st.error(f"データ読み込みに失敗しました: {exc}")
    st.stop()

st.sidebar.header("基本フィルタ")

min_date = data["購入日"].min().date()
max_date = data["購入日"].max().date()
date_range = st.sidebar.date_input(
    "購入日",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

regions = st.sidebar.multiselect("地域", sorted(data["地域"].dropna().unique().tolist()))
categories = st.sidebar.multiselect(
    "購入カテゴリー", sorted(data["購入カテゴリー"].dropna().unique().tolist())
)

filtered = data[(data["購入日"].dt.date >= start_date) & (data["購入日"].dt.date <= end_date)]
if regions:
    filtered = filtered[filtered["地域"].isin(regions)]
if categories:
    filtered = filtered[filtered["購入カテゴリー"].isin(categories)]

if filtered.empty:
    st.warning("条件に一致するデータがありません。フィルタを調整してください。")
    st.stop()

# M1 KPI
total_sales = filtered["購入金額"].sum()
avg_sales = filtered["購入金額"].mean()
txn_count = len(filtered)

k1, k2, k3 = st.columns(3)
k1.metric("総売上", format_yen(total_sales))
k2.metric("平均購入単価", format_yen(avg_sales))
k3.metric("取引件数", f"{txn_count:,}件")

st.divider()

# M1 集計と可視化
monthly_sales = filtered.groupby("年月", as_index=False)["購入金額"].sum().sort_values("年月")
cat_sales = (
    filtered.groupby("購入カテゴリー", as_index=False)["購入金額"]
    .sum()
    .sort_values("購入金額", ascending=False)
)
region_sales = (
    filtered.groupby("地域", as_index=False)["購入金額"].sum().sort_values("購入金額", ascending=False)
)

g1, g2, g3 = st.columns(3)
with g1:
    fig_monthly = px.line(monthly_sales, x="年月", y="購入金額", markers=True, title="月次売上推移")
    st.plotly_chart(fig_monthly, use_container_width=True)
with g2:
    fig_cat = px.bar(cat_sales, x="購入カテゴリー", y="購入金額", title="カテゴリ別売上")
    st.plotly_chart(fig_cat, use_container_width=True)
with g3:
    fig_region = px.bar(region_sales, x="地域", y="購入金額", title="地域別売上")
    st.plotly_chart(fig_region, use_container_width=True)
