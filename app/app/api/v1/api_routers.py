from fastapi import APIRouter

from app.api.v1.endpoints.admin import login_router as admin_login_router
from app.api.v1.endpoints.admin import router as admin_router
from app.api.v1.endpoints.agents import router as agents_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.channels import router as channels_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.payments import router as payments_router
from app.api.v1.endpoints.servers import router as servers_router
from app.api.v1.endpoints.skills import router as skills_router
from app.api.v1.endpoints.subscriptions import router as subscriptions_router
from app.api.v1.endpoints.tariffs import router as tariffs_router
from app.api.v1.endpoints.tools import router as tools_router
from app.api.v1.endpoints.users import router as users_router

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(auth_router)
v1_router.include_router(users_router)
v1_router.include_router(tariffs_router)
v1_router.include_router(payments_router)
v1_router.include_router(agents_router)
v1_router.include_router(skills_router)
v1_router.include_router(tools_router)
v1_router.include_router(channels_router)
v1_router.include_router(subscriptions_router)
v1_router.include_router(servers_router)
v1_router.include_router(admin_login_router)
v1_router.include_router(admin_router)
v1_router.include_router(health_router)
