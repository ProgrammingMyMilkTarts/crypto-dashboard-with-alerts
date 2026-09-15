from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.alerts import router as alert_router
from api.routes.prices import router as price_router
from core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables when the app starts.
    init_db()
    yield


app = FastAPI(
    title="Crypto Price Tracker API",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS so the backend can be called by frontend apps or local tools.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all route groups for the API.
app.include_router(price_router)
app.include_router(alert_router)


@app.get("/")
def root():
    return {"status": "online", "message": "Crypto Tracker Backend"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)