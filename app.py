"""
Punto de entrada alternativo (app.py).
Importa y expone la instancia principal de FastAPI de main.py.
"""

from main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

