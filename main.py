from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import driver
from routers import insights, newsletters, subscribers, tracking


@asynccontextmanager
async def lifespan(app: FastAPI):
    driver.verify_connectivity()
    yield
    driver.close()


app = FastAPI(title="Coral Data Newsletter API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(subscribers.router)
app.include_router(newsletters.router)
app.include_router(tracking.router)
app.include_router(insights.router)


@app.get("/health")
def health():
    return {"status": "ok"}
