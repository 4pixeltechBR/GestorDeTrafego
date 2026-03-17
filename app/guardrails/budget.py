"""
Guardrails de Orçamento (Budget Hard-Caps).

Impede que os agentes (ou falhas na comunicação com a API)
gastem mais do que o limite mensal/diário definido no .env.
"""

import logging
from datetime import datetime, date

from app.core.database import get_db
from config.settings import settings

logger = logging.getLogger(__name__)


class BudgetExceededError(Exception):
    """Exceção levantada quando o orçamento excede o guardrail."""
    pass


async def check_budget_guardrails(new_campaign_daily_budget_brl: float) -> bool:
    """
    Verifica se a criação de uma nova campanha violará os hard-caps.

    Regras:
    1. O budget da nova campanha não pode exceder o BUDGET_MAX_DIARIO sozinho.
    2. A soma do budget diário de todas as campanhas ATIVAS + o novo budget
       não pode exceder o BUDGET_MAX_DIARIO total do sistema.

    Args:
        new_campaign_daily_budget_brl: O orçamento projetado da nova campanha em Reais.

    Raises:
        BudgetExceededError: Se violar as regras.

    Returns:
        True se estiver seguro.
    """
    max_diario = settings.budget_max_diario

    # 1. Checagem Simples da Nova Campanha
    if new_campaign_daily_budget_brl > max_diario:
        logger.warning(
            f"[Guardrail] ❌ CAMPANHA BLOQUEADA: Budget de R${new_campaign_daily_budget_brl:.2f} "
            f"excede o limite rígido diário de R${max_diario:.2f}."
        )
        raise BudgetExceededError(
            f"Orçamento da campanha (R${new_campaign_daily_budget_brl:.2f}) "
            f"excede seu teto diário global (R${max_diario:.2f})."
        )

    # 2. Checagem Sistêmica (Todas as campanhas ativas no DB)
    try:
        db = await get_db()
        cursor = await db.execute(
            "SELECT SUM(daily_budget) as total_active_budget FROM campaigns WHERE status = 'ACTIVE'"
        )
        row = await cursor.fetchone()
        await db.close()

        total_active_budget = row["total_active_budget"] if row and row["total_active_budget"] else 0.0

    except Exception as e:
        logger.error(f"[Guardrail] Erro ao consultar banco de dados: {e}")
        raise BudgetExceededError("Falha de segurança ao validar budget no banco local. Operação abortada.")

    projetado_total = total_active_budget + new_campaign_daily_budget_brl

    if projetado_total > max_diario:
        logger.warning(
            f"[Guardrail] ❌ CAMPANHA BLOQUEADA: O sistema já gasta R${total_active_budget:.2f}/dia. "
            f"Adicionar R${new_campaign_daily_budget_brl:.2f} excederia o teto de R${max_diario:.2f}."
        )
        raise BudgetExceededError(
            f"Risco de overspending! Limite diário: R${max_diario:.2f}. "
            f"Comprometido atual: R${total_active_budget:.2f}. "
            f"Tentativa de +R${new_campaign_daily_budget_brl:.2f} rejeitada pelo Guardrail."
        )

    logger.info(
        f"[Guardrail] ✅ Budget Seguro: R${projetado_total:.2f} / R${max_diario:.2f} (Diário)"
    )
    return True


async def check_monthly_spending() -> float:
    """Calcula quanto o sistema já gastou no mês corrente consultando o DB de métricas."""
    current_month = datetime.now().strftime("%Y-%m")
    
    try:
        db = await get_db()
        cursor = await db.execute(
            "SELECT SUM(spend) as month_spend FROM metrics WHERE date LIKE ?",
            (f"{current_month}-%",)
        )
        row = await cursor.fetchone()
        await db.close()

        spent = row["month_spend"] if row and row["month_spend"] else 0.0
        
        if spent > settings.budget_max_mensal:
            logger.critical(
                f"[Guardrail] 🚨 EMERGÊNCIA: Gasto Mensal (R${spent:.2f}) excedeu o Teto Rígido "
                f"(R${settings.budget_max_mensal:.2f}). O sistema deveria pausar todas as campanhas imediatamente!"
            )
            
        return spent

    except Exception as e:
        logger.error(f"[Guardrail] Erro ao consultar gasto mensal: {e}")
        return 0.0
