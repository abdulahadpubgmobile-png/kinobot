from aiogram import Router
from app.handlers.users import user_router
from app.handlers.admin import admin_router

main_router = Router()
main_router.include_routers(admin_router, user_router)
