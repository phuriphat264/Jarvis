from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1 import auth, conversations, system, memories, tools, agent, files
from app.core.config import settings

from contextlib import asynccontextmanager
from app.services.reminder_scheduler import scheduler
from app.services.proactive_engine import proactive_engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    await scheduler.start()
    await proactive_engine.start()
    yield
    await scheduler.stop()
    await proactive_engine.stop()

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": str(exc)
            }
        }
    )

from app.api.v1 import auth, conversations, system, memories, tools, agent, files, voice, personal_os, integrations, actions, briefing, iot, edge, intelligence, personalization

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(conversations.router, prefix="/api/v1/conversations", tags=["conversations"])
app.include_router(memories.router, prefix="/api/v1/memories", tags=["memories"])
app.include_router(tools.router, prefix="/api/v1/tools", tags=["tools"])
app.include_router(agent.router, prefix="/api/v1/agent", tags=["agent"])
app.include_router(files.router, prefix="/api/v1/files", tags=["files"])
app.include_router(voice.router, prefix="/api/v1/voice", tags=["voice"])
app.include_router(personal_os.router, prefix="/api/v1/personal", tags=["personal_os"])
app.include_router(integrations.router, prefix="/api/v1/integrations", tags=["integrations"])
app.include_router(actions.router, prefix="/api/v1/actions", tags=["actions"])
app.include_router(briefing.router, prefix="/api/v1/briefing", tags=["briefing"])
app.include_router(iot.router, prefix="/api/v1/iot", tags=["iot"])
app.include_router(edge.router, prefix="/api/v1/edge", tags=["edge"])
app.include_router(intelligence.router, prefix="/api/v1/intelligence", tags=["intelligence"])
app.include_router(personalization.router, prefix="/api/v1/personalization", tags=["personalization"])
app.include_router(system.router, prefix="/api/v1/system", tags=["system"])
app.include_router(system.router, prefix="", tags=["health"]) # /health

@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.APP_NAME} API"}
