from aiogram import Router
from app.handlers.admin.add_movie import router as add_movie_router
from app.handlers.admin.panel import router as panel_router
from app.handlers.admin.channels import router as channels_router
from app.handlers.admin.import_json import router as import_json_router
from app.handlers.admin.import_csv import router as import_csv_router
from app.handlers.admin.edit_movie import router as edit_movie_router
from app.handlers.admin.ads import router as ads_router
from app.handlers.admin.series import router as series_router
from app.handlers.admin.stats import router as stats_router

admin_router = Router()
admin_router.include_routers(add_movie_router, panel_router, channels_router, import_json_router, import_csv_router, edit_movie_router, ads_router, series_router, stats_router)
