"""
Agente Analista — Interpreta métricas de campanhas e recomenda ações.

Análise multi-fator: ROAS, CPA, CTR, frequência, fase de aprendizado.
"""

import json
import logging
from typing import Optional

from app.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

# Diagnóstico local antes de chamar LLM (economiza tokens)
def _quick_diagnose(metrics: dict, benchmarks: Optional[dict] = None) -> str:
    """
    Diagnóstico rápido baseado em regras determinísticas.
    Retorna SAUDAVEL, ATENCAO ou CRITICO.
    """
    roas = metrics.get("roas", 0)
    ctr = metrics.get("ctr", 0)
    frequency = metrics.get("frequency", 0)
    clicks = metrics.get("clicks", 0)

    # Regra 1: Dados insuficientes
    if clicks < 100:
        return "ATENCAO"  # Amostra pequena, não concluir nada

    # Regra 2: ROAS catastrófico (perdendo dinheiro)
    if roas > 0 and roas < 0.5:
        return "CRITICO"

    # Regra 3: Frequência muito alta (público saturado)
    if frequency > 4.5:
        return "ATENCAO"

    # Regra 4: CTR extremamente baixo
    if ctr < 0.3:
        return "ATENCAO"

    return "SAUDAVEL"


class AnalystAgent(BaseAgent):
    AGENT_ID = "analyst"
    AGENT_NAME = "Analista"
    PROMPT_FILE = "analyst.md"

    async def analyze(
        self,
        metrics: dict,
        campaign_name: str = "Campanha",
        nicho: str = "servicos",
        days_running: int = 0,
        benchmarks: Optional[dict] = None,
        campaign_id: Optional[str] = None,
    ) -> dict:
        """
        Analisa métricas de uma campanha e retorna diagnóstico + recomendações.

        Args:
            metrics: Dict com spend, impressions, clicks, cpc, ctr, roas, etc.
            campaign_name: Nome da campanha para contexto
            nicho: Nicho do negócio (para benchmarks)
            days_running: Dias que a campanha está rodando
            benchmarks: Benchmarks do nicho (cpc_medio, roas_minimo, etc.)
            campaign_id: ID interno (para audit log)

        Returns:
            dict com diagnóstico, recomendação e sugestões
        """
        # Diagnóstico rápido local (sem LLM)
        quick_diag = _quick_diagnose(metrics, benchmarks)
        logger.info(
            f"[{self.AGENT_NAME}] Diagnóstico rápido para '{campaign_name}': "
            f"{quick_diag} ({metrics.get('clicks', 0)} cliques)"
        )

        # Monta contexto rico para o LLM
        context_parts = [
            f"CAMPANHA: {campaign_name}",
            f"NICHO: {nicho}",
            f"DIAS RODANDO: {days_running}",
            f"DIAGNÓSTICO RÁPIDO (determinístico): {quick_diag}",
        ]

        if days_running < 3:
            context_parts.append(
                "⚠️ ATENÇÃO: Campanha em FASE DE APRENDIZADO (< 3 dias). "
                "Métricas podem ser instáveis. Evite pausar."
            )

        if benchmarks:
            context_parts.append(
                f"BENCHMARKS DO NICHO:\n"
                f"  CPC médio: R${benchmarks.get('cpc_medio', '?')}\n"
                f"  CPC máximo aceitável: R${benchmarks.get('cpc_maximo_aceitavel', '?')}\n"
                f"  ROAS mínimo: {benchmarks.get('roas_minimo', '?')}x\n"
                f"  Frequência máxima: {benchmarks.get('frequencia_maxima', '?')}"
            )

        context = "\n".join(context_parts)
        metrics_formatted = json.dumps(metrics, ensure_ascii=False, indent=2)

        result = await self.think(
            user_message=(
                f"Analise estas métricas de campanha do Meta Ads:\n\n"
                f"```json\n{metrics_formatted}\n```\n\n"
                f"Retorne um JSON com: resumo, métricas, diagnóstico, "
                f"recomendação (MANTER/OTIMIZAR/PAUSAR) e sugestões específicas."
            ),
            context=context,
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        try:
            analysis = json.loads(result["content"])
            analysis["_meta"] = {
                "llm_provider": result["provider"],
                "llm_model": result["model"],
                "tokens_used": result["tokens_used"],
                "quick_diagnose": quick_diag,
                "days_running": days_running,
            }

            recomendacao = analysis.get("recomendacao", {}).get("acao", "?")
            logger.info(
                f"[{self.AGENT_NAME}] Recomendação para '{campaign_name}': "
                f"{recomendacao} (via {result['provider']})"
            )
            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"[{self.AGENT_NAME}] Erro ao parsear análise: {e}")
            return {
                "resumo": f"Erro ao processar análise. Diagnóstico rápido: {quick_diag}",
                "diagnostico": quick_diag,
                "recomendacao": {
                    "acao": "MANTER",
                    "motivo": "Erro ao processar. Mantendo por segurança.",
                    "sugestoes": ["Revisar manualmente as métricas."],
                },
                "_meta": {
                    "llm_provider": result.get("provider", "?"),
                    "llm_model": result.get("model", "?"),
                    "erro": str(e),
                    "quick_diagnose": quick_diag,
                },
            }
