# LTE Band 41 RCA Application

A production-grade application for analyzing LTE Band 41 network anomalies. Features AI-powered root cause analysis, anomaly detection, parameter drift monitoring, and natural language querying.

## Architecture

- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS + shadcn/ui
- **Backend**: FastAPI (Python) with REST API
- **Engine**: Python PM parser + LTE B41 RCA engine
- **AI Module**: GPT summaries, ML anomaly detection, drift detection, and NLQ

## Features

### Core Functionality

- Ingest Ericsson ENM PM counter files (.xml.gz, .gz, .zip, .xml)
- Parse and analyze PM XML data (supports multiple Ericsson XML formats)
- Detect anomalies (Transport/TIMING, Microwave ACM, TDD misalignment, etc.)
- Validate new-site post-integration performance
- Interactive dashboards with time-series charts
- Automatic file cleanup (files older than 24 hours are removed)

### AI-Enhanced Features

- **AI RCA Summary**: Human-readable explanations of root cause analysis
- **ML Anomaly Detection**: IsolationForest-based detection of unexpected patterns
- **Parameter Drift Detection**: Baseline comparison for parameter changes
- **Natural Language Query**: Ask questions about KPI data in plain English

## Project Structure

```
pLTE-Band41-RCA/
├── frontend/                 # Next.js 14 Frontend
│   ├── app/
│   │   ├── dashboard/        # Dashboard page with KPI charts
│   │   ├── rca/              # RCA analysis results page
│   │   ├── upload/           # File upload page
│   │   ├── ask-ai/           # Natural language query interface
│   │   ├── help/             # KPI reference and help page
│   │   ├── layout.tsx        # Root layout with navigation
│   │   ├── page.tsx          # Home page
│   │   └── globals.css       # Global styles with Tailwind
│   ├── components/
│   │   ├── ui/               # shadcn/ui components
│   │   ├── navigation.tsx    # Main navigation bar
│   │   ├── theme-provider.tsx
│   │   └── theme-toggle.tsx  # Dark/light mode toggle
│   └── lib/
│       └── utils.ts          # Utility functions
│
├── backend/                  # FastAPI Backend
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example         # Environment variables template
│   ├── uploads/             # Temporary file storage
│   └── baselines/           # Baseline storage for drift detection
│
├── engine/                   # RCA Engine
│   ├── __init__.py
│   ├── parser.py            # Ericsson PM XML parser
│   └── rca.py               # Root Cause Analysis logic
│
├── ai/                       # AI Features Module
│   ├── __init__.py
│   ├── gpt_summary.py       # Feature A: GPT-based RCA summary
│   ├── anomaly_detector.py  # Feature B: ML anomaly detection
│   ├── drift_detector.py    # Feature C: Parameter drift detection
│   └── nlq.py               # Feature D: Natural language query
│
├── README.md
├── LICENSE
└── .gitignore
```

## Setup

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- pip

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your OpenAI API key if using GPT-4o
# ALLOW_CLOUD=1
# OPENAI_API_KEY=your-api-key-here
```

5. Start the FastAPI server:
```bash
uvicorn main:app --reload
```

The backend will run on `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

Frontend runs on `http://localhost:3000`

### Verify Installation

- Backend health check: `http://localhost:8000/health`
- Frontend: `http://localhost:3000`
- Test OpenAI connection (if configured): `python test_openai_connection.py`

## Usage

### Basic Workflow

1. Navigate to `/upload` page
2. Upload an Ericsson PM XML file (.xml.gz)
3. View analysis results on `/dashboard` and `/rca` pages
4. Ask questions on `/ask-ai` page

### Pages

- **`/upload`** - Upload PM XML files for analysis (.xml.gz, .gz, .zip, .xml)
- **`/dashboard`** - View KPI metrics, time-series charts, and site comparisons
- **`/rca`** - Detailed root cause analysis with AI enhancements
- **`/ask-ai`** - Natural language query interface powered by GPT-4o (when configured)
- **`/help`** - KPI parameters reference, ideal values, thresholds, and root cause classifications

## API Endpoints

### Core Endpoints

- `GET /health` - Health check
- `POST /upload` - Upload PM XML file
- `POST /analyze` - Parse and analyze PM data with AI enhancements

### AI Endpoints

- `POST /ask-ai` - Answer natural language questions about KPI data

**Request:**

```json
{
  "question": "What is the root cause?",
  "kpi_data": [...],
  "rca_result": {...}
}
```

**Response:**

```json
{
  "answer": "The primary root cause is...",
  "confidence": 0.85
}
```

## AI Features

The application includes four AI-enhanced features that work together to provide comprehensive network analysis.

### Feature A: GPT-Based RCA Summary

**Location:** `ai/gpt_summary.py`

Converts deterministic RCA results into clear, human-readable explanations.

**Features:**
- Supports local mode (default) and remote GPT mode (if `ALLOW_CLOUD=1`)
- Generates structured summaries with root cause, severity, KPIs, anomalies, drift, and recommendations
- Automatically called in `/analyze` endpoint
- Results displayed in RCA page as "AI RCA Summary" card

### Feature B: Anomaly Detection Model

**Location:** `ai/anomaly_detector.py`

Uses IsolationForest ML model to detect unexpected behavior from PM counter patterns.

**Features:**
- Uses scikit-learn's IsolationForest
- Detects spikes, drops, timing-related anomalies, and PRB/throughput bursts
- Returns anomaly scores, flags, and periods
- Automatically called in `/analyze` endpoint
- Results displayed in RCA page as "Anomaly Detection (ML Model)" card

### Feature C: Parameter Drift Detection

**Location:** `ai/drift_detector.py`

Detects parameter drift for new site post-integration and daily O&M comparison.

**Features:**
- Compares current KPIs against baseline
- Auto-creates baseline from first ingest if none exists
- Detects parameter changes, TDD shifts, RF behavior changes, and timing anomalies
- Returns drift score (0.0 to 1.0) and parameters of interest
- Baselines stored in `backend/baselines/` directory
- Results displayed in RCA page as "Parameter Drift Detection" card

### Feature D: Natural Language Query

**Location:** `ai/nlq.py`

Allows users to ask questions about KPI behavior in plain English.

**Features:**
- **Local Mode (default)**: Rule-based pattern matching for common question types
- **GPT-4o Mode**: Advanced LLM-powered responses when `ALLOW_CLOUD=1` and `OPENAI_API_KEY` is set

**GPT-4o Features:**
- Professional, report-quality responses suitable for network operations teams
- Automatic LaTeX cleanup (converts equations to plain text)
- Context-aware analysis with KPI data and RCA results
- Structured responses with calculations, recommendations, and actionable insights
- Confidence scoring for all responses
- Answers questions about root causes, KPI values, trends, anomalies, and site comparisons

**Integration:**
- New endpoint: `POST /ask-ai`
- New frontend page: `/ask-ai`
- Accepts question, KPI data, and RCA results as context

## Environment Variables

- `ALLOW_CLOUD=1` - Enable remote GPT/LLM usage (default: disabled, uses local models)
- `OPENAI_API_KEY` - OpenAI API key required when `ALLOW_CLOUD=1` to use GPT-4o for Ask AI feature

**Note:** 
- When `ALLOW_CLOUD=1` is set and `OPENAI_API_KEY` is configured, the Ask AI feature will use GPT-4o for more intelligent, context-aware responses
- GPT-4o responses are automatically cleaned of LaTeX notation and formatted as professional reports
- If API key is missing or errors occur, the system gracefully falls back to a rule-based local system
- Requires OpenAI library version 2.7.1 or higher (automatically installed via requirements.txt)

### Setting Environment Variables

#### Option 1: Using .env file (Recommended)

1. Create a `.env` file in the `backend/` directory:
   ```bash
   cd backend
   ```

2. Create `.env` with the following content:
   ```env
   ALLOW_CLOUD=1
   OPENAI_API_KEY=your-api-key-here
   ```

3. The backend will automatically load these variables when it starts.

#### Option 2: Windows PowerShell (Temporary - Current Session Only)

```powershell
$env:ALLOW_CLOUD="1"
$env:OPENAI_API_KEY="your-api-key-here"
```

#### Option 3: Windows Command Prompt (Temporary - Current Session Only)

```cmd
set ALLOW_CLOUD=1
set OPENAI_API_KEY=your-api-key-here
```

#### Option 4: Windows System Environment Variables (Permanent)

1. Open System Properties → Advanced → Environment Variables
2. Add new User or System variables:
   - Variable: `ALLOW_CLOUD`, Value: `1`
   - Variable: `OPENAI_API_KEY`, Value: `your-api-key-here`
3. Restart your terminal/IDE for changes to take effect

## RCA Root Cause Classifications

The system detects and classifies the following root causes:

1. Transport/TIMING Fault
2. Microwave ACM Fade
3. TDD Frame Misalignment
4. RF Interference / Sector Overshoot
5. Congestion
6. RF Quality Degradation
7. Parameter Mismatch
8. New-Site Integration Issue
9. CPE-Specific Issue

## KPI Thresholds

- RRC Setup Success Rate: ≥ 95%
- ERAB Setup Success Rate: ≥ 98%
- PRB Utilization Avg: < 70%
- PRB Utilization P95: < 85%
- SINR Avg: > 5 dB
- SINR P10: > 0 dB
- BLER P95: < 10%
- Paging Success Rate: ≥ 95%
- S1 Setup Failure Rate: < 1%
- Cell Availability: ≥ 99%

## File Format

The application supports multiple Ericsson ENM PM counter file formats:

- **`.xml.gz`** - Compressed XML (recommended)
- **`.gz`** - GZIP compressed files
- **`.zip`** - ZIP archives containing XML files
- **`.xml`** - Plain XML files

The XML should contain:
- PM measurement containers (`<measCollecFile>`, `<mdc>`, or standard Ericsson formats)
- Timestamp information
- Site/cell identifiers
- KPI counter measurements

**File Storage:**
- Uploaded files are stored temporarily in `backend/uploads/`
- Files older than 24 hours are automatically cleaned up
- Files are processed and removed after analysis

## Development

### Backend Development

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend
npm run dev
```

## Ask AI Capabilities

When GPT-4o is enabled, Ask AI can answer questions about:

- **Root Cause Analysis**: "What is causing the performance issues?"
- **KPI Calculations**: "What is the RRC setup success rate?"
- **Trends**: "How is PRB utilization trending?"
- **Anomalies**: "Are there any unusual patterns in the data?"
- **Site Comparisons**: "Compare performance across different sites"
- **Recommendations**: "What should I do to fix this issue?"
- **Technical Explanations**: "Explain the root cause in simple terms"

All responses are formatted as professional reports with:
- Specific calculations and formulas (plain text, no LaTeX)
- Actionable recommendations
- KPI thresholds and targets
- Site-specific analysis
- Confidence scores

## Documentation

- [KPI_PARAMETERS.md](KPI_PARAMETERS.md) - Complete KPI parameters reference with thresholds, ideal values, and Ericsson counter mappings

## Troubleshooting

### Ask AI Not Using GPT-4o

1. Verify `.env` file exists in `backend/` directory
2. Check that `ALLOW_CLOUD=1` and `OPENAI_API_KEY` are set
3. Restart backend server after configuration changes
4. Check backend console for debug messages: `[Ask AI] ALLOW_CLOUD=1, has_api_key=True, use_local=False`
5. Run `python test_openai_connection.py` to test OpenAI connectivity

### LaTeX in Responses

If you see LaTeX notation (e.g., `\[ \frac{128}{140} \]`), the cleanup function should automatically convert it. If it persists:
1. Restart backend server
2. Check that OpenAI library is version 2.7.1 or higher: `pip show openai`
3. Update if needed: `pip install --upgrade openai`

### File Upload Issues

- Ensure file format is supported: `.xml.gz`, `.gz`, `.zip`, or `.xml`
- Check backend console for parsing errors
- Verify XML structure matches Ericsson ENM PM format
- Check `backend/uploads/` directory for uploaded files

## License

This project is available for portfolio and demonstration purposes. See LICENSE file for details.
