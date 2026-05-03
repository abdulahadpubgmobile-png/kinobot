from aiogram import Router
from app.handlers.users.start import router as start_router
from app.handlers.users.movies import router as movies_router

user_router = Router()
user_router.include_routers(start_router, movies_router)
