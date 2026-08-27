from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "backend is running"}
from db import engine

@app.get("/test-db")
def test_db():
    try:
        with engine.connect() as connection:
            return {"database": "connected successfully"}
    except Exception as e:
        return {"database": "connection failed", "error": str(e)}