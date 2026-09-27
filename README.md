# IBM Bob 2.0: AI Debugging & Testing Agent — Backend Service

**Role**: Backend Developer (Dinakaran)  
**Team**: Kumarvel (Lead/Architect) | Abinav (AI/Agent) | Shlok (Frontend) | Jagadeep (DevOps) | Dinakaran (Backend)  
**Core Principles**: Fast ⚡ + Safe 🛡️ + Secure 🔐 + Reliable ✅  

---

## 🏗️ Architecture & Features

- **Framework**: Python 3.12 + FastAPI (high-performance asynchronous execution)
- **Input Validation**: Pydantic v2 schemas + payload byte limits (`MAX_CODE_SIZE_BYTES`)
- **Rate Limiting**: `slowapi` IP-based throttling preventing API abuse
- **AI Agent Integration**: Flexible adapter for Abinav's AI service with built-in fallback/mock mode for offline testing
- **Safe Execution**: AST syntax analysis without executing arbitrary code on host server
- **Database / History**: Async SQLAlchemy (PostgreSQL in production, SQLite for fast zero-dependency local dev)
- **CORS Support**: Pre-configured for Shlok's Frontend (`http://localhost:3000`, `http://localhost:5173`)
- **DevOps Ready**: Multi-stage non-root `Dockerfile`, `docker-compose.yml`, and `/api/v1/health` probes for Jagadeep

---

## 📁 Project Structure

```text
IBM/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── analyze.py        # POST /api/v1/analyze (Core analysis endpoint)
│   │       │   ├── health.py         # GET /api/v1/health (DevOps probe)
│   │       │   └── history.py        # GET /api/v1/history (Past analysis audit)
│   │       └── router.py             # Route aggregator
│   ├── core/
│   │   ├── config.py                 # Pydantic BaseSettings & .env management
│   │   ├── logging.py                # Safe structured logging
│   │   └── security.py               # Rate limiting & API key dependency
│   ├── db/
│   │   ├── session.py                # Async engine & session provider
│   │   └── models.py                 # SQLAlchemy tables (AnalysisRecord)
│   ├── schemas/
│   │   ├── analyze.py                # Request & response contracts
│   │   └── common.py                 # Standard API response envelopes
│   ├── services/
│   │   ├── ai_agent.py               # Abinav's AI Agent client + mock engine
│   │   └── sanitizer.py              # Payload validator & AST safety checks
│   └── main.py                       # FastAPI entrypoint, middlewares & exception handlers
├── tests/
│   ├── conftest.py                   # Async test client & in-memory SQLite fixtures
│   ├── test_analyze.py               # Unit & integration tests for analysis
│   └── test_health.py                # Health & root endpoint tests
├── .env.example                      # Environment variables template
├── requirements.txt                  # Python dependencies
├── Dockerfile                        # Multi-stage container file
└── docker-compose.yml                # Backend + PostgreSQL container setup
```

---

## 🚀 Quickstart (Local Development)

### 1. Activate Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Run Database & API Server
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Interactive ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

### 3. Run Test Suite
```powershell
pytest -v
```

---

## 📡 API Specification

### `POST /api/v1/analyze`
Submits source code for bug detection, root cause explanation, fix suggestion, and automated test cases.

#### Request Body
```json
{
  "code": "def divide(a, b):\n    return a / b",
  "language": "python",
  "file_name": "math_utils.py",
  "context_description": "Crashes on zero input",
  "generate_test_cases": true
}
```

#### Response (200 OK)
```json
{
  "success": true,
  "message": "Code analyzed successfully",
  "data": {
    "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "language": "python",
    "summary": "Analysis completed successfully. Identified 1 issue(s) and generated 2 test case(s).",
    "total_bugs_detected": 1,
    "bugs": [
      {
        "bug_id": "BUG-A1B2C3",
        "title": "ZeroDivisionError Potential",
        "severity": "high",
        "line_number": 2,
        "description": "Division operation does not check if divisor 'b' is zero.",
        "root_cause": "Unchecked arithmetic division.",
        "suggested_fix": "Add boundary check: if b == 0: raise ValueError(...)",
        "fixed_code_snippet": "if b == 0:\n    raise ValueError('Divisor cannot be 0')\nreturn a / b"
      }
    ],
    "fixed_code": "def divide(a, b):\n    if b == 0:\n        raise ValueError('Divisor cannot be 0')\n    return a / b",
    "test_cases": [
      {
        "test_id": "TC-101",
        "name": "test_standard_division",
        "test_code": "def test_std(): assert divide(10, 2) == 5",
        "test_type": "unit"
      },
      {
        "test_id": "TC-102",
        "name": "test_zero_division",
        "test_code": "def test_zero(): with pytest.raises(ValueError): divide(10, 0)",
        "test_type": "edge_case"
      }
    ],
    "analysis_time_ms": 12.4,
    "status": "completed"
  }
}
```

---

## 🤝 Team Integration Notes

### For Shlok (Frontend Developer)
- CORS is already enabled for your local dev ports (`3000` & `5173`).
- All responses use standard `{ success: true, message: "...", data: {...} }` format.
- Connect your frontend state directly to `POST /api/v1/analyze` and `GET /api/v1/history`.

### For Abinav (AI / Agent Developer)
- The backend delegates to `app/services/ai_agent.py`.
- In `.env`, set `MOCK_AI_AGENT=False` and point `AI_AGENT_SERVICE_URL` to your AI agent service endpoint.
- If your service is offline, backend gracefully falls back to safety rules without crashing.

### For Jagadeep (DevOps Integration)
- Run production stack: `docker compose up --build`
- Dockerfile runs as an unprivileged user (`appuser`).
- Automated container health check probe is active at `GET /api/v1/health`.
