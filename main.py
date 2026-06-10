from fastapi import FastAPI
from db.database import engine
from db import models
from routers.v1 import tasks, sessions, auth, teacher, admin
from core.config import settings
from fastapi.middleware.cors import CORSMiddleware


models.Base.metadata.create_all(bind=engine)

router_prefix = "/api/v1"
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router, prefix=router_prefix)
app.include_router(sessions.router, prefix=router_prefix)
app.include_router(auth.router, prefix=router_prefix)
app.include_router(teacher.router, prefix=router_prefix)
app.include_router(admin.router, prefix=router_prefix)
