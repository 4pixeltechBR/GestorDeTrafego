"""
Agente Orquestrador — Cérebro do sistema.

Interpreta briefings de campanha e coordena os outros agentes.
"""

import json
import logging
from typing import Optional

from app.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseAgent):
    AGENT_ID = "orchestrator"
    AGENT_NAME = "Orquestrador"
    PROMPT_FILE = "orchestrator.md"

    # Mapeamento de palavras-chave para nichos
    NICHE_KEYWORDS = {
        "auto_center": [
            "pneu", "oficina", "mecânica", "carro", "veículo",
            "óleo", "freio", "revisão", "auto center", "funilaria",
        ],
        "clinica": [
            "clínica", "médico", "dentista", "saúde", "consulta",
            "exame", "fisioterapia", "psicólogo", "nutricionista",
        ],
        "restaurante": [
            "restaurante", "comida", "delivery", "hamburger",
            "pizza", "marmita", "cardápio", "refeição", "café",
        ],
        "ecommerce": [
            "loja", "produto", "venda", "comprar", "e-commerce",
            "loja online", "site", "marketplace",
        ],
        "servicos": [
            "serviço", "conserto", "instalação", "limpeza",
            "pintura", "reforma", "elétrica", "hidráulica",
        ],
    }

    def _detect_niche(self, briefing: str) -> str:
        """Detecta nicho baseado em palavras-chave do briefing."""
        briefing_lower = briefing.lower()
        for niche, keywords in self.NICHE_KEYWORDS.items():
            if any(kw in briefing_lower for kw in keywords):
                return niche
        return "servicos"  # default

    async def parse_briefing(
        self,
        briefing: str,
        campaign_id: Optional[str] = None,
    ) -> dict:
        """
        Interpreta um briefing de campanha e extrai parâmetros estruturados.

        Args:
            briefing: Texto livre do usuário descrevendo a campanha
            campaign_id: ID da campanha (para audit log)

        Returns:
            dict com todos os parâmetros extraídos e estruturados
        """
        # Detecta nicho localmente (rápido, sem LLM)
        detected_niche = self._detect_niche(briefing)
        logger.info(
            f"[{self.AGENT_NAME}] Nicho detectado localmente: {detected_niche}"
        )

        # Monta contexto para o LLM
        context = f"Nicho detectado automaticamente: {detected_niche}"

        result = await self.think(
            user_message=(
                f"Interprete este briefing de campanha de tráfego pago:\n\n"
                f"---\n{briefing}\n---\n\n"
                f"Retorne um JSON estruturado com todos os parâmetros extraídos."
            ),
            context=context,
            temperature=0.3,  # Baixo — queremos precisão
            response_format={"type": "json_object"},
        )

        try:
            parsed = json.loads(result["content"])
            parsed["_meta"] = {
                "llm_provider": result["provider"],
                "llm_model": result["model"],
                "tokens_used": result["tokens_used"],
                "detected_niche_local": detected_niche,
            }
            logger.info(
                f"[{self.AGENT_NAME}] Briefing interpretado com sucesso. "
                f"Objetivo: {parsed.get('objetivo', '?')}"
            )
            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"[{self.AGENT_NAME}] Erro ao parsear JSON: {e}")
            # Retorna estrutura mínima funcional
            return {
                "produto": briefing[:100],
                "nicho": detected_niche,
                "canal": "meta", # fallback safe
                "objetivo": "OUTCOME_TRAFFIC",
                "orcamento_diario": 30.0,
                "publico_alvo": {
                    "persona_inferida": "Massa Geral de Teste",
                    "idade_min": 25,
                    "idade_max": 55,
                    "renda_estimada": "Qualquer",
                    "interesses": [],
                    "localizacao": "Brasil",
                },
                "proximo_passo": "copywriter",
                "instrucao_agente": f"Crie 2 copies para: {briefing[:80]}",
                "_erro": str(e),
                "_meta": {
                    "llm_provider": result.get("provider", "?"),
                    "llm_model": result.get("model", "?"),
                },
            }
