from fastapi import FastAPI
from app.routers import web, ws

app = FastAPI()

# incluir routers
app.include_router(web.router)
app.include_router(ws.router)
