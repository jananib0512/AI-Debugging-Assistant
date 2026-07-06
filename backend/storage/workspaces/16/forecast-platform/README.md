# ForecastIQ — Universal Forecasting Platform

A web-based AI/ML forecasting platform where users can upload datasets, perform automated data validation, exploratory data analysis (EDA), data preprocessing, train multiple forecasting models (ARIMA, Prophet, XGBoost, LSTM, etc.), compare model performance side-by-side, and generate comprehensive reports — all through an interactive workflow with step-by-step guidance.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, JavaScript, Bootstrap 5, Plotly.js |
| Backend | Python Flask, REST API |
| Database | SQLite (SQLAlchemy ORM) |
| ML/AI | Pandas, NumPy, Scikit-learn, Statsmodels, Prophet, XGBoost, TensorFlow/Keras |
| Visualization | Plotly, Matplotlib |
| Reporting | ReportLab (PDF), OpenPyXL (Excel), Pandas (CSV) |

---

## Features (Phases 1–8)

### Phase 1 — System Architecture
- Complete architecture document (`PHASE1_ARCHITECTURE.md`)
- Folder structure, database schema, API blueprint, development roadmap

### Phase 2 — Authentication
- User registration with validation
- Login/logout with session management
- Werkzeug password hashing (pbkdf2:sha256)
- Protected routes with `@login_required` decorator
- User profile page

### Phase 3 — Dataset Upload & Validation
- Upload CSV, XLS, XLSX files (drag-and-drop, max 50MB)
- Dataset preview with paginated data table
- Upload history with status badges
- 9 validation checks:
  - Empty dataset detection
  - Missing value analysis (count + percentage)
  - Duplicate row detection
  - Empty column detection
  - Duplicate column detection
  - Data type classification (numeric, categorical, date, text)
  - Date column auto-detection
  - Dataset size analysis

### Phase 4 — EDA Engine (Dual Mode)

**Automatic EDA:**
- Dataset overview (rows, columns, memory usage)
- Statistical summary (mean, median, mode, std, variance, quartiles, skewness, kurtosis)
- Missing value analysis
- Correlation matrix + heatmap
- Outlier detection (IQR + Z-Score)
- Distribution analysis (histograms, boxplots)
- Categorical analysis (frequency, bar charts, pie charts)
- Time series analysis (trend, date range, frequency)
- Feature insights (target suggestions, high correlations, outlier-prone columns)
- 7+ interactive Plotly chart types
- HTML report generation with embedded images

**Manual EDA:**
- Select specific statistics, analyses, and visualizations via checkboxes
- Generate only what you need

### Phase 5 — Data Preprocessing
- Dual mode: **Automatic** (one-click) or **Manual** (custom configuration)
- Missing value handling: mean, median, mode, drop, forward fill, backward fill, constant value
- Outlier treatment: IQR, Z-Score, Winsorization, capping
- Encoding: label encoding, one-hot encoding
- Scaling: standard scaler, min-max scaler, robust scaler
- Automatic train/test split (80/20)
- Before/after comparison (original vs. processed shape)

### Phase 6 — Forecasting Engine
- Multiple model support:
  - **Traditional:** ARIMA, SARIMA, ETS (Exponential Smoothing), Theta, Naive, Seasonal Naive
  - **Machine Learning:** Random Forest, Gradient Boosting, XGBoost
  - **Deep Learning:** LSTM
- Automated time series detection (date column + frequency)
- Train/test split evaluation
- Performance metrics: MAE, RMSE, MAPE, R²
- Future period forecasting (configurable horizon)
- Model-specific parameter display (e.g., ARIMA order, LSTM layers)
- Interactive actual vs. predicted charts (Plotly)

### Phase 7 — Model Comparison
- Side-by-side ranking of all trained models
- Performance metrics table (MAE, RMSE, MAPE, R², Training Time)
- Smart Insights generation (best model analysis, trend direction, consistency, variance, speed)
- Interactive charts: RMSE, MAE, MAPE, R², Training Time comparison
- Actual vs. Predicted visualization per model (with forecast extension)
- **Next Step navigation** → Proceed to Reports

### Phase 8 — Reports & Workflow Completion
- **Full Report Dashboard** (`/reports/<dataset_id>`):
  - Dataset Summary (name, rows, columns, upload date)
  - Validation Summary (status, errors, missing values)
  - EDA Summary (data quality score, charts, column type counts)
  - Preprocessing Summary (methods applied for missing values, outliers, encoding, scaling)
  - Forecast Summary (best model, horizon, target column)
  - Comparison Summary (ranked models with all metrics)
  - **Smart Insights** — auto-generated insights from real data quality and model performance
- **Download Center** — PDF, CSV, Excel formats
- **Workflow Completion Page** (`/workflow/completed/<dataset_id>`):
  - Celebratory summary with all stats
  - 7-step workflow table with statuses
  - Action cards: View Reports, Download Report, Analyze Another Dataset, Back to Dashboard
- **Analysis History** — tracks completed workflows per user, displayed on dashboard
- **Enhanced Dashboard** — recent analyses, best models used, total forecasts, analyses completed

---

## Project Structure

```
forecast_platform/
├── app.py                  # Flask app factory
├── config.py               # Configuration
├── database.py             # SQLAlchemy init
├── run.py                  # Entry point
├── requirements.txt
│
├── routes/
│   ├── auth.py             # Authentication + dashboard
│   ├── dataset_routes.py   # Upload, validate, preview
│   ├── eda.py              # EDA (auto/manual/report)
│   ├── preprocessing.py    # Preprocessing (auto/manual)
│   ├── forecasting.py      # Forecasting setup + dashboard
│   ├── comparison.py       # Model comparison
│   └── reports.py          # Reports + workflow completion
│
├── models/
│   ├── user_model.py
│   ├── dataset_model.py
│   ├── validation_report_model.py
│   ├── eda_report_model.py
│   ├── preprocessing_report_model.py
│   ├── forecast_report_model.py
│   ├── comparison_report_model.py
│   ├── report_model.py
│   ├── analysis_history_model.py
│   └── activity_log_model.py
│
├── services/
│   ├── dataset_service.py      # File upload, preview
│   ├── validation_service.py   # Data quality checks
│   ├── eda_service.py          # EDA computation & reports
│   ├── chart_service.py        # Plotly + Matplotlib charts
│   ├── preprocessing_service.py # Missing values, encoding, scaling
│   ├── forecasting_service.py  # Model training & forecasting
│   ├── comparison_service.py   # Model comparison & ranking
│   ├── report_service.py       # Full report generation (CSV/XLSX/PDF)
│   ├── workflow_service.py     # Multi-step workflow state machine
│   └── activity_service.py     # Activity logging
│
├── utils/
│   └── file_utils.py       # File validation, secure naming
│
├── templates/
│   ├── base.html           # Bootstrap 5 base template
│   ├── login.html, register.html
│   ├── dashboard.html, profile.html
│   ├── upload_dataset.html, upload_history.html
│   ├── dataset_preview.html, validation_report.html
│   ├── eda_mode.html, eda_dashboard.html
│   ├── manual_eda.html, eda_summary.html, eda_charts.html
│   ├── preprocessing_mode.html, preprocessing_dashboard.html
│   ├── forecast_mode.html, forecast_setup.html, forecast_dashboard.html
│   ├── compare_results.html
│   ├── report_view.html
│   └── workflow_completed.html
│
├── static/
│   ├── css/style.css
│   └── js/main.js
│
├── data/uploads/           # Uploaded dataset files
├── reports/eda_reports/    # Generated EDA reports & charts
└── instance/               # SQLite database
```

---

## Workflow

```
Register → Login → Upload Dataset → Validate
    → EDA (Auto / Manual)
    → Preprocessing (Auto / Manual)
    → Forecasting (model selection + training)
    → Comparison (rank models, view metrics, charts)
    → Reports Dashboard (download PDF/CSV/Excel)
    → Workflow Completed (summary + action cards)
```

Each step has a **workflow tracker** showing progress, with navigation buttons to move forward/backward. Steps are locked until prerequisites are completed.

---

## API Routes

### Authentication
| Route | Methods | Description |
|-------|---------|-------------|
| `/` | GET | Landing / redirect |
| `/login` | GET, POST | User login |
| `/register` | GET, POST | User registration |
| `/logout` | GET | Logout |
| `/dashboard` | GET | User dashboard (with analysis history) |
| `/profile` | GET | User profile |

### Datasets
| Route | Methods | Description |
|-------|---------|-------------|
| `/upload` | GET, POST | Upload dataset |
| `/datasets` | GET | Upload history |
| `/dataset/<id>` | GET | Dataset detail + preview |
| `/dataset/<id>/preview` | GET | Full preview |
| `/dataset/<id>/validate` | POST | Run validation |
| `/validation-report/<id>` | GET | View validation report |
| `/dataset/<id>/delete` | POST | Delete dataset |

### EDA
| Route | Methods | Description |
|-------|---------|-------------|
| `/eda-mode/<id>` | GET | EDA mode selection |
| `/eda-auto/<id>` | POST | Run automatic EDA |
| `/eda-manual/<id>` | GET, POST | Run manual EDA |
| `/eda-dashboard/<id>` | GET | EDA results dashboard |
| `/eda-summary/<id>` | GET | EDA summary |
| `/eda-charts/<id>` | GET | Chart gallery |
| `/generate-eda-report/<id>` | POST | Generate HTML report |
| `/download-eda-report/<id>` | GET | Download report |

### Preprocessing
| Route | Methods | Description |
|-------|---------|-------------|
| `/preprocessing/mode/<id>` | GET | Preprocessing mode selection |
| `/preprocessing/auto/<id>` | POST | Run automatic preprocessing |
| `/preprocessing/manual/<id>` | GET, POST | Run manual preprocessing |
| `/preprocessing/dashboard/<id>` | GET | Preprocessing results |

### Forecasting
| Route | Methods | Description |
|-------|---------|-------------|
| `/forecasting/mode/<id>` | GET | Forecasting mode selection |
| `/forecasting/setup/<id>` | GET, POST | Configure forecast parameters |
| `/forecasting/run/<id>` | POST | Train models |
| `/forecasting/dashboard/<id>` | GET | Forecast results + charts |

### Comparison
| Route | Methods | Description |
|-------|---------|-------------|
| `/compare/<id>` | GET, POST | Run model comparison |
| `/compare/results/<id>` | GET | Comparison results dashboard |
| `/compare/api/model/<id>/<name>` | GET | API: model actual vs predicted data |
| `/compare/download/<id>/<format>` | GET | Download comparison (CSV/XLSX/PDF) |

### Reports
| Route | Methods | Description |
|-------|---------|-------------|
| `/reports/<id>` | GET | Full report dashboard |
| `/workflow/completed/<id>` | GET | Workflow completion page |
| `/reports/download/<id>/<format>` | GET | Download report (CSV/XLSX/PDF) |

---

## Database Tables

| Table | Purpose |
|-------|---------|
| `users` | User accounts (id, username, email, password_hash, created_at) |
| `datasets` | Uploaded file metadata (file_name, rows, columns, size, upload_date) |
| `validation_reports` | Validation results (missing values, duplicates, column types, outliers) |
| `eda_reports` | EDA analysis records (mode, chart count, report path) |
| `preprocessing_reports` | Preprocessing steps (mode, steps applied, original/processed shapes) |
| `forecast_reports` | Forecast model results (model name, horizon, metrics) |
| `comparison_reports` | Model comparison results (best model, ranking, metrics) |
| `reports` | Generated report records |
| `analysis_history` | Completed workflow history per user |
| `activity_log` | User activity tracking (actions, timestamps) |

---

## Installation

### Prerequisites
- Python 3.11+
- pip

### Setup

```bash
# Clone or navigate to the project
cd forecast_platform

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate    # Linux/Mac
venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt

# Run the application
python run.py
```

Open **http://127.0.0.1:5000** in your browser.

### Optional Dependencies

For deep learning models (LSTM), install TensorFlow:
```bash
pip install tensorflow
```

For Prophet:
```bash
pip install prophet
```

For PDF report generation, ReportLab is included in the base requirements.

---

## Testing

```bash
# Run all tests
python -m pytest

# Run specific test files
python -m pytest tests/test_reports.py -v
python -m pytest tests/test_comparison.py -v
python -m pytest tests/test_forecasting.py -v

# Run with coverage
pip install pytest-cov
python -m pytest --cov=. --cov-report=term-missing
```

---

## Development Roadmap

| Phase | Status | Features |
|-------|--------|----------|
| Phase 1 | ✅ | System architecture, folder structure, database design |
| Phase 2 | ✅ | User authentication, session management |
| Phase 3 | ✅ | Dataset upload, validation engine |
| Phase 4 | ✅ | Dual-mode EDA (auto + manual), chart generation, reports |
| Phase 5 | ✅ | Data preprocessing (missing values, scaling, encoding, train/test split) |
| Phase 6 | ✅ | Forecasting engine (ARIMA, Prophet, XGBoost, LSTM, RF, GBR) |
| Phase 7 | ✅ | Model comparison, ranking, charts, smart insights |
| Phase 8 | ✅ | Full reports (PDF/CSV/Excel), workflow completion, analysis history |

---

## Security

- Password hashing via Werkzeug (pbkdf2:sha256)
- Server-side session management (no large data in client cookies)
- Secure file upload with UUID renaming
- Input validation on all forms
- SQLAlchemy ORM (parameterized queries, no raw SQL)
- File type and size restrictions (CSV/XLS/XLSX, 50MB max)

---

## License

MIT
