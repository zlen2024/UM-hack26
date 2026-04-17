# Run Backend (Windows PowerShell)
cd backend
uv venv
.\venv\Scripts\Activate
uv pip install -r requirements.txt
uvicorn main:app --reload