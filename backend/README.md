certificate_verifier/
├── requirements.txt         # Dependencies
├── app/
│   ├── __init__.py
│   ├── main.py              # Orchestrator & API Entrypoint
│   ├── schemas.py           # Pydantic Models (Data Contracts)
│   └── agents/
│       ├── __init__.py
│       ├── forensics.py     # Agent 1: Manipulation check
│       ├── extraction.py    # Agent 2: OCR & Regex
│       └── verification.py  # Agent 3: URL & Domain Validation