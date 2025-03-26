from app.routers.users import router as users_router
from app.routers.visitors import router as visitors_router
from app.routers.access_logs import router as access_logs_router
from app.routers.incidents import router as incidents_router

__all__ = [
    "users_router",
    "visitors_router",
    "access_logs_router",
    "incidents_router"
]
