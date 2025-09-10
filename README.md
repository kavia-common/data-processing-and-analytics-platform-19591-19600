# data-processing-and-analytics-platform-19591-19600

Backend API (FastAPI) runs on port 3001.

Quickstart:
1. Create a virtualenv and install dependencies:
   pip install -r backend_api/requirements.txt

2. Copy .env.example to .env and adjust values as needed:
   cp backend_api/.env.example backend_api/.env

3. Run the API locally:
   python -m uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload

Key Endpoints:
- GET / : Health check
- POST /api/uploads : Upload CSV (multipart form-data, field: file)
- POST /api/analytics/stats : Compute statistics for a dataset
- POST /api/analytics/process : Filter/limit records
- POST /api/reports/summary : Generate and (optionally) email summary report
- POST /api/visualize/chart.png : Generate chart PNG (scatter|line|bar)