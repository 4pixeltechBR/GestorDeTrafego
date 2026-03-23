"""
bot.py — Entry point do GestorDeTrafego.

Uso:
    python bot.py

Requer:
    - .env configurado com TELEGRAM_BOT_TOKEN e TELEGRAM_ADMIN_CHAT_ID
    - Pelo menos uma API Key de IA (GROQ_API_KEY ou GOOGLE_AI_KEY)
"""

import asyncio
import logging
import sys
from pathlib import Path

# Garante que o diretório raiz está no path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters

from app.core.database import init_db
from app.scheduler.tasks import init_scheduler
from app.bot.handlers import handle_message, handle_callback
from config.settings import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


async def main():
    # Validações mínimas
    if not settings.telegram_bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN não configurado no .env!")
        sys.exit(1)

    if not settings.telegram_admin_chat_id:
        logger.error("❌ TELEGRAM_ADMIN_CHAT_ID não configurado no .env!")
        sys.exit(1)

    if not settings.available_providers:
        logger.warning("⚠️  Nenhuma API Key de IA configurada! Configure ao menos GROQ_API_KEY.")

    # Inicializa banco de dados
    await init_db()

    # Constrói o bot
    app = (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .build()
    )

    # Handler para mensagens de texto (briefings)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Handler para cliques nos botões inline
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Scheduler para relatório diário às 08:00
    scheduler = init_scheduler(app.bot)
    scheduler.start()

    logger.info("=" * 55)
    logger.info(f"🚀 {settings.app_name} iniciado!")
    logger.info(f"   Provedores IA: {settings.available_providers or '⚠️ Nenhum'}")
    logger.info(f"   Meta Ads: {'✅' if settings.has_meta_config else '⚠️ Não configurado'}")
    logger.info(f"   Modo: {settings.approval_mode.upper()}")
    logger.info(f"   Budget máx: R${settings.budget_max_diario:.0f}/dia")
    logger.info("   Aguardando mensagens no Telegram...")
    logger.info("=" * 55)

    try:
        await app.run_polling(drop_pending_updates=True)
    finally:
        scheduler.shutdown()
        logger.info("🛑 Bot encerrado.")


if __name__ == "__main__":
    asyncio.run(main())
