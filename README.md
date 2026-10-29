# UK Wind Forecast Accuracy: January 2026

A web app for a day-ahead power buyer. It shows the latest wind forecast available at the
decision deadline and measures how accurate those forecasts were against actual generation.

**Live app:** YOUR-LINK

## How it works
- Data: Elexon BMRS, national wind only. Actuals from FUELHH (30-minute), forecasts from WINDFOR (hourly, many versions per target hour).
- Decision cutoff: 09:20 on the day before delivery (EPEX GB day-ahead gate closure). Configurable in the app (09:50 = N2EX).
- For each delivery hour, the forecast used is the most recent one published at or before the cutoff. Later forecasts are ignored to avoid data leakage.
- Actuals are averaged to hourly so they line up with the hourly forecasts.
- Metrics: bias, MAE, RMSE, error by hour of day, error by day, and 90th/95th percentile safety margins.

## Files and directories
- `backend/main.py`: FastAPI app with the data cleaning, cutoff logic and two endpoints (`/api/forecast`, `/api/errors`)
- `backend/data/`: raw Elexon CSV downloads for January 2026
- `frontend/`: React (Vite) app with number cards and charts
- `public/`: built React files served by Vercel
- `app.py`: Vercel entrypoint
- `Dockerfile`: builds the React app and the Python backend into one image
- `requirements.txt`: Python dependencies
- `notes/`: exploration scripts used to study the data

## Run with Docker
    docker build -t wind-app .
    docker run -p 8000:8000 wind-app
Then open http://localhost:8000

## Run locally without Docker
Backend:
    cd backend
    pip install -r requirements.txt
    python3 -m uvicorn main:app --reload
Frontend (second terminal):
    cd frontend
    npm install
    npm run dev
Then open http://localhost:5173

## Assumptions and limits
- One month of data, so the error statistics are estimates, not guarantees.
- The 09:20 cutoff comes from published gate-closure times and may change; check the exchanges.

## AI tools
This project was built with the help of copilot, used for explanations, code generation and review.
