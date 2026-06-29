# 💰 AI Personal Finance Analyzer

A production-quality, AI-powered personal finance dashboard built with **Streamlit**, **Python**, **MySQL**, and **Google Gemini**.

---

## ✨ Features

| Feature | Tech |
|---|---|
| CSV upload & preprocessing | Pandas + NumPy |
| Auto expense categorisation | Rule-based regex engine |
| MySQL persistence | SQLAlchemy 2.0 + PyMySQL |
| Interactive charts | Plotly |
| Anomaly detection | Scikit-Learn Isolation Forest |
| Financial Health Score | Custom weighted algorithm |
| AI insights & recommendations | Google Gemini 1.5 Flash |
| Professional UI | Streamlit + custom CSS |

---

## 🗂 Project Structure

```
finance_analyzer/
├── main.py                        # Streamlit entry point
├── requirements.txt
├── .env.example                   # Copy → .env and fill in secrets
├── config/
│   ├── __init__.py
│   └── settings.py                # Typed config from .env
├── app/
│   ├── models/
│   │   └── transaction.py         # SQLAlchemy ORM model
│   ├── services/
│   │   ├── database.py            # DB init, session, bulk insert
│   │   └── gemini_service.py      # Gemini API wrapper
│   ├── utils/
│   │   ├── preprocessor.py        # CSV cleaning & normalisation
│   │   ├── categorizer.py         # Regex-based categorisation
│   │   ├── analytics.py           # KPIs & aggregations
│   │   ├── anomaly_detector.py    # Isolation Forest
│   │   └── charts.py              # Plotly chart factories
│   ├── components/
│   │   └── ui.py                  # Reusable Streamlit widgets
│   └── pages/
│       ├── overview.py            # Page 1 — KPI Overview
│       ├── expense_analysis.py    # Page 2 — Expense Deep-dive
│       └── ai_insights.py         # Page 3 — AI Recommendations
└── data/
    └── samples/
        └── sample_transactions.csv
```

---

## 🚀 Quick Start

### 1. Clone & install dependencies

```bash
git clone <repo>
cd finance_analyzer
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env:
#   DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
#   GEMINI_API_KEY  ← get from https://aistudio.google.com/app/apikey
```

### 3. Start MySQL

Make sure your MySQL server is running. The app auto-creates the database and tables on first launch.

### 4. Run the app

```bash
streamlit run main.py
```

Open [http://localhost:8501](http://localhost:8501)

---

## 📊 Supported CSV Formats

The preprocessor auto-detects these column patterns:

| Pattern | Example Banks |
|---|---|
| `Date, Description, Debit, Credit` | HDFC, ICICI, SBI |
| `Date, Narration, Amount, Type` | Axis, Kotak |
| `Transaction Date, Particulars, Withdrawal, Deposit` | PNB, BOI |
| `Date, Details, Amount` (signed) | Many neobanks |

---

## 🤖 AI Insights (Gemini)

Set `GEMINI_API_KEY` in `.env`. Get a free key at:  
👉 [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

The AI generates:
- Overall financial assessment
- Key spending concerns
- 5 personalised savings tips
- 30-day action plan
- Positive highlights

---

## 📈 Financial Health Score

Computed from 4 weighted dimensions:

| Dimension | Weight | Ideal |
|---|---|---|
| Savings rate | 40 pts | ≥ 30% |
| Expense ratio | 25 pts | < 70% of income |
| Anomaly rate | 20 pts | 0 anomalies |
| Spend consistency | 15 pts | Low monthly variance |

---

## 🛡️ Anomaly Detection

Uses **Isolation Forest** (scikit-learn) on:
- Transaction amount
- Day of week
- Day of month

Contamination factor: 5% (configurable in `config/settings.py`)

---

## 📝 License

MIT
