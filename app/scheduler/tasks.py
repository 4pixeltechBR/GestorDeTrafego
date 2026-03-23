"""
Scheduler — Tarefas em segundo plano.

Job diário às 08:00: busca métricas, analisa, envia relatório no Telegram.
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.database import get_db
from app.meta.insights import fetch_campaign_metrics
from app.agents.analyst import AnalystAgent
from app.bot.formatter import format_daily_report

logger = logging.getLogger(__name__)

# Referência ao bot Telegram (injetada no init_scheduler)
_bot = None


async def daily_analysis_job():
    """
    Job diário de análise.
    Busca campanhas publicadas, analisa métricas, envia relatório.
    """
    logger.info("[Scheduler] Iniciando análise diária...")

    try:
        db = await get_db()
        # CORRIGIDO: busca campanhas publicadas (meta_campaign_id preenchido)
        # independente do status local, pois o usuário pode ter ativado no Meta
        cursor = await db.execute(
            "SELECT * FROM campaigns WHERE meta_campaign_id IS NOT NULL AND status != 'DELETED'"
        )
        campaigns = await cursor.fetchall()
        await db.close()

        if not campaigns:
            logger.info("[Scheduler] Nenhuma campanha publicada para analisar.")
            return

        analyst = AnalystAgent()
        report_lines = ["<b>📊 Relatório Diário de Tráfego</b>", "━━━━━━━━━━━━━━━━━━━", ""]

        for campaign in campaigns:
            meta_campaign_id = campaign["meta_campaign_id"]
            name = campaign["name"]
            niche = campaign["niche"] or "servicos"

            logger.info(f"[Scheduler] Analisando: '{name}'")

            metrics = await fetch_campaign_metrics(meta_campaign_id)

            analysis = await analyst.analyze(
                metrics=metrics,
                campaign_name=name,
                niche=niche,
                days_running=7,
            )

            report_block = format_daily_report(name, metrics, analysis)
            report_lines.append(report_block)
            report_lines.append("")

        full_report = "\n".join(report_lines)

        # Envia via bot Telegram
        if _bot:
            from config.settings import settings
            await _bot.send_message(
                chat_id=settings.telegram_admin_chat_id,
                text=full_report,
                parse_mode="HTML",
            )
            logger.info("[Scheduler] Relatório enviado com sucesso.")
        else:
            logger.warning("[Scheduler] Bot não configurado. Relatório não enviado.")
            logger.info(f"[Scheduler] Relatório:\n{full_report}")

    except Exception as e:
        logger.error(f"[Scheduler] Erro no job diário: {e}", exc_info=True)


def init_scheduler(bot=None) -> AsyncIOScheduler:
    """
    Inicializa o scheduler.

    Args:
        bot: Instância do Bot Telegram para envio de relatórios.
    """
    global _bot
    _bot = bot

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        daily_analysis_job,
        trigger=CronTrigger(hour=8, minute=0),
        id="daily_insight_analysis",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    logger.info("[Scheduler] Job diário configurado (08:00).")
    return scheduler
