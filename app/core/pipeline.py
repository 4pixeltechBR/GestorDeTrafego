"""
Pipeline — Orquestra os agentes sem camada HTTP.

Extrai a lógica de app/api/routes.py para uma função Python pura,
permitindo que seja chamada tanto pelo bot Telegram quanto pela API REST.
"""

import logging
from typing import Optional

from app.agents.orchestrator import OrchestratorAgent
from app.agents.copywriter import CopywriterAgent
from app.agents.compliance import ComplianceAgent
from app.agents.executor import ExecutorAgent
from app.agents.keyword_planner import KeywordPlannerAgent
from app.guardrails.budget import check_budget_guardrails, BudgetExceededError
from config.settings import settings

logger = logging.getLogger(__name__)


class ComplianceBlockedError(Exception):
    """Levantada quando o Compliance rejeita as copies."""
    def __init__(self, problemas: list):
        self.problemas = problemas
        super().__init__(f"Compliance bloqueou: {problemas}")


def _normalize_publico(raw) -> dict:
    """Garante que publico_alvo é sempre um dict válido."""
    if isinstance(raw, str):
        return {
            "persona_inferida": raw,
            "idade_min": 18,
            "idade_max": 65,
            "interesses": [],
            "localizacao": "Brasil",
        }
    if not isinstance(raw, dict):
        return {
            "persona_inferida": "Público geral",
            "idade_min": 18,
            "idade_max": 65,
            "interesses": [],
            "localizacao": "Brasil",
        }
    return raw


async def run_campaign_pipeline(
    briefing: str,
    canal: str = "auto",
) -> dict:
    """
    Executa o pipeline completo de criação de campanha.

    Args:
        briefing: Texto livre do usuário descrevendo a campanha.
        canal: "auto", "meta" ou "google_search".

    Returns:
        dict com orchestration, copies (TODAS), payloads, canal, compliance.

    Raises:
        BudgetExceededError: Se o orçamento exceder o guardrail.
        ComplianceBlockedError: Se o Compliance rejeitar as copies.
        RuntimeError: Se o LLM Router esgotar todos os provedores.
    """
    logger.info(f"[Pipeline] Iniciando. Briefing: {briefing[:60]}...")

    # 1. Orquestrador
    orchestrator = OrchestratorAgent()
    orch_res = await orchestrator.parse_briefing(briefing)

    orcamento = orch_res.get("orcamento_diario", 50.0)
    canal_decidido = orch_res.get("canal", "meta") if canal == "auto" else canal
    publico = _normalize_publico(orch_res.get("publico_alvo", {}))

    logger.info(
        f"[Pipeline] Orquestrador: produto={orch_res.get('produto')}, "
        f"canal={canal_decidido}, orçamento=R${orcamento}"
    )

    # 2. Guardrail antes de gastar tokens
    await check_budget_guardrails(orcamento)

    # 3. Copywriter
    copywriter = CopywriterAgent()
    copies_result = await copywriter.generate_copies(
        produto=orch_res.get("produto"),
        nicho=orch_res.get("nicho"),
        publico_alvo=publico,
        objetivo=orch_res.get("objetivo"),
        canal=canal_decidido,
    )
    copies = copies_result.get("opcoes", [])

    if not copies:
        raise RuntimeError("Copywriter não gerou nenhuma opção de copy.")

    # 4. Compliance
    compliance = ComplianceAgent()
    comp_res = await compliance.validate_copy(copies, orch_res.get("nicho"))

    if not comp_res.get("aprovado"):
        raise ComplianceBlockedError(comp_res.get("problemas", []))

    # 5. Keywords (Google Search apenas)
    keywords_payload = None
    if canal_decidido == "google_search":
        kw = KeywordPlannerAgent()
        keywords_payload = await kw.generate_keywords(
            produto=orch_res.get("produto"),
            nicho=orch_res.get("nicho"),
            publico_alvo=publico,
            orcamento_diario=orcamento,
        )

    # 6. Executor — monta JSON para CADA copy (não só a primeira)
    executor = ExecutorAgent()
    payloads = []
    for copy in copies:
        payload = await executor.build_campaign_json(
            produto=orch_res.get("produto"),
            nicho=orch_res.get("nicho"),
            copy=copy,
            orcamento_diario=orcamento,
            publico_alvo=publico,
            objetivo=orch_res.get("objetivo"),
            canal=canal_decidido,
            keywords_payload=keywords_payload,
        )
        payloads.append(payload)

    logger.info(
        f"[Pipeline] Concluído. {len(copies)} copies geradas, "
        f"{len(payloads)} payloads prontos."
    )

    result = {
        "orchestration": orch_res,
        "copies": copies,
        "payloads": payloads,
        "canal": canal_decidido,
        "compliance": comp_res,
        "orcamento": orcamento,
        "produto": orch_res.get("produto"),
        "nicho": orch_res.get("nicho"),
    }

    # Se modo auto, registra intenção de execução direta (sem botão de aprovação)
    # O handler do Telegram usa esse flag para pular a etapa de confirmação
    result["auto_execute"] = (settings.approval_mode == "auto")

    return result
