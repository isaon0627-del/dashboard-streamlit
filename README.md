# ダッシュボードストリームリット

`sample-data.csv` を使った購買分析用の Streamlit ダッシュボードです。

## 主な機能
- KPI表示（総売上、平均購入単価、取引件数、月平均売上、家電カテゴリ比率）
- フィルタ（期間、地域、購入カテゴリー、性別、支払方法、年齢レンジ）
- 可視化（時系列、構成比、セグメント分析、散布図、ヒートマップ）
- 明細表示とCSVダウンロード

## 動作環境
- Python 3.12 以降（推奨）
- Streamlit
- Pandas
- Plotly

## セットアップ
1. 仮想環境を作成
2. 必要パッケージをインストール

```bash
pip install streamlit pandas plotly
```

## 実行方法
プロジェクトルートで以下を実行します。

```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` を開くとダッシュボードを確認できます。

## データファイル
- `date/sample-data.csv`

## 主要ファイル
- `app.py`: ダッシュボード本体
- `dashboard_visualization_plan.md`: 可視化設計
- `dashboard_requirements_definition.md`: 要件定義
- `dashboard_implementation_tickets.md`: 実装チケット
