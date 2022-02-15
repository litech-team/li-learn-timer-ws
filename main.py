import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

if os.environ.get("PYTHON_ENV") == "production":
    root_path = "/ws"
else:
    root_path = ""

app = FastAPI(root_path=root_path)


@app.get("/")
async def root():
    return HTMLResponse("<h1>Welcome! This is Root Page!</h1>")

@app.get("/about")
async def about():
    return HTMLResponse("<h1>Welcome! This is About Page!</h1>")