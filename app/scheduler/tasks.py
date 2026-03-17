"""
Módulo do Agendador (Scheduler).

Configura tarefas em segundo plano (APScheduler) para o loop principal:
1. Buscar dados de insights de todas as campanhas ativas.
2. Analisar as métricas com o Agente Analista.
3. Enviar relatório consolidado pelo Telegram.
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.database import get_db
from app.meta.insights import fetch_campaign_metrics
from app.agents.analyst import AnalystAgent
from app.notifications.telegram_bot import notifier

logger = logging.getLogger(__name__)


async def daily_analysis_job():
    """
    Job Diário de Análise.
    - Puxa campanhas ativas no DB local.
    - Busca insights na API do Meta.
    - Analisa com LLM Analyst.
    - Notifica no Telegram o diagnóstico final.
    """
    logger.info("[Scheduler] \u23f1\ufe0f Iniciando \u00e1nalise di\u00e1ria de campanhas ativas...")
    
    try:
        db = await get_db()
        cursor = await db.execute("SELECT * FROM campaigns WHERE status = 'ACTIVE'")
        active_campaigns = await cursor.fetchall()
        await db.close()

        if not active_campaigns:
            logger.info("[Scheduler] Nenhuma campanha ativa encontrada para an\u00e1lise.")
            return

        analyst = AnalystAgent()
        report_lines = []

        for campaign in active_campaigns:
            meta_campaign_id = campaign["meta_campaign_id"]
            name = campaign["name"]
            niche = campaign["niche"] or "servicos"
            
            logger.info(f"[Scheduler] Analisando: '{name}' ({meta_campaign_id})")
            
            # Busca métricas
            metrics = await fetch_campaign_metrics(meta_campaign_id)
            
            # Avalia
            analysis_result = await analyst.analyze(
                metrics=metrics,
                campaign_name=name,
                niche=niche,
                days_running=7 # Todo: Fórmular baseado no created_at
            )
            
            diag = analysis_result.get("diagnostico", "UNKNOWN")
            rec = analysis_result.get("recomendacao", {}).get("acao", "UNKNOWN")
            smry = analysis_result.get("resumo", "Sem resumo.")
            
            # Adiciona ao relatório
            report_lines.append(f"<b>\ud83d\udce3 {name}</b>")
            report_lines.append(f"<b>Diagn\u00f3stico:</b> {diag} | <b>Recomenda\u00e7\u00e3o:</b> {rec}")
            report_lines.append(f"<i>{smry}</i>")
            report_lines.append("") # Quebra de linha
            
        # Consolida
        final_report = "\n".join(report_lines)
        
        # Envia no Telegram
        await notifier.send_daily_report(final_report)
        logger.info("[Scheduler] \u2705 An\u00e1lise di\u00e1ria conclu\u00edda e enviada.")
        
    except Exception as e:
        logger.error(f"[Scheduler] \u274c Erro no job di\u00e1rio de an\u00e1lise: {e}")


def init_scheduler() -> AsyncIOScheduler:
    """Inicializa as rotinas em background."""
    scheduler = AsyncIOScheduler()
    
    # 1. Job Diário: Executa todos os dias às 08:00 AM
    scheduler.add_job(
        daily_analysis_job,
        trigger=CronTrigger(hour=8, minute=0),
        id="daily_insight_analysis",
        replace_existing=True,
        misfire_grace_time=3600 # Dá 1h de chance de rodar se o bot estava offline as 8:00
    )
    
    logger.info("[Scheduler] Cron Jobs configurados (An\u00e1lise Di\u00e1ria s\u00e0s 08:00)")
    return scheduler
