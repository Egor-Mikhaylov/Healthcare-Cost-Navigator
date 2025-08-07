from fastapi import FastAPI

from .routers import ask, providers

app = FastAPI(title="Healthcare Cost Navigator")

app.include_router(providers.router)
app.include_router(ask.router)
