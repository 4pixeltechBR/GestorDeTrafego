"""
Gestor de Tráfego IA — Aplicação Principal (FastAPI).
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config.settings import settings, BASE_DIR
from app.core.database import init_db
from app.scheduler.tasks import init_scheduler
from app.notifications.telegram_bot import notifier
from app.api.routes import router as api_router

# Configura logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle: Inicializa serviços no startup e limpa no shutdown."""
    # --- STARTUP ---
    logger.info("=" * 60)
    logger.info(f"🚀 {settings.app_name} iniciando...")
    logger.info(f"   Provedores de IA: {settings.available_providers or '⚠️ Nenhum configurado!'}")
    logger.info(f"   Meta Ads: {'✅ Configurado' if settings.has_meta_config else '⚠️ Não configurado'}")
    logger.info(f"   Telegram: {'✅ Ativo' if settings.has_telegram else '⚠️ Desativado'}")
    logger.info(f"   Modo: {settings.approval_mode.upper()}")
    logger.info(f"   Budget Max Diário: R$ {settings.budget_max_diario:.2f}")
    logger.info("=" * 60)

    # Inicializa banco de dados
    await init_db()

    # Fase 4 — Inicializar Bot Telegram
    await notifier.ping()

    # Fase 4 — Inicializar Scheduler (análise diária às 08:00)
    scheduler = init_scheduler()
    scheduler.start()

    yield

    # --- SHUTDOWN ---
    logger.info(f"🛑 {settings.app_name} finalizando...")
    scheduler.shutdown()


# Cria app FastAPI
app = FastAPI(
    title=settings.app_name,
    description="Copiloto de Tráfego Pago com IA — Open Source",
    version="0.1.0",
    lifespan=lifespan,
)

# Adiciona Rotas da API
app.include_router(api_router, prefix="/api")

# Servir arquivos estáticos (Dashboard)
ui_path = BASE_DIR / "ui"
if ui_path.exists():
    app.mount("/static", StaticFiles(directory=str(ui_path)), name="static")


@app.get("/")
async def root():
    """Redireciona para o Dashboard."""
    index_path = ui_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {
        "app": settings.app_name,
        "status": "online",
        "version": "0.1.0",
        "docs": "/docs",
        "providers": settings.available_providers,
    }


@app.get("/api/health")
async def health():
    """Health check do sistema."""
    return {
        "status": "ok",
        "providers": settings.available_providers,
        "meta_configured": settings.has_meta_config,
        "telegram_active": settings.has_telegram,
        "approval_mode": settings.approval_mode,
    }
