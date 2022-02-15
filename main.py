from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()


@app.get("/")
async def root():
    return HTMLResponse("<h1>Welcome! This is Root Page!</h1>")

@app.get("/about")
async def about():
    return HTMLResponse("<h1>Welcome! This is About Page!</h1>")