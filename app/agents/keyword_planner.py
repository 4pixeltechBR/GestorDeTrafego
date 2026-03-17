"""
Agente Keyword Planner — A IA especialista do Google Search.

Gera listas de palavras-chave, correspondências, lances de CPC e negativas.
"""

import json
import logging
from typing import Optional

from app.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class KeywordPlannerAgent(BaseAgent):
    AGENT_ID = "keyword_planner"
    AGENT_NAME = "Keyword Planner"
    PROMPT_FILE = "keyword_planner.md"

    async def generate_keywords(
        self,
        produto: str,
        nicho: str,
        publico_alvo: dict,
        orcamento_diario: float,
    ) -> dict:
        """
        Dada a estratégia do orquestrador, elabora os agrupamentos Search.
        """
        context = f"""
NICHO ESTRATÉGICO: {nicho}
PRODUTO/OFERTA: {produto}
ORÇAMENTO DIÁRIO: R${orcamento_diario:.2f}

PERSONA (Desenhada pelo Orquestrador):
{publico_alvo.get('persona_inferida', 'N/A')}
- Idade: {publico_alvo.get('idade_min')}-{publico_alvo.get('idade_max')}
- Renda: {publico_alvo.get('renda_estimada', 'N/A')}
- Local: {publico_alvo.get('localizacao', 'Brasil')}
"""

        logger.info(f"[{self.AGENT_NAME}] Invocando Modelo para gerar Keywords do {produto[:30]}...")

        result = await self.think(
            user_message=(
                "Utilize esta estratégia omnichannel para processar a mineração de palavras.\n\n"
                "Retorne o JSON bruto de Keywords limitando-se a no máximo 15 positivas de alta performance e 10 negativas."
            ),
            context=context,
            temperature=0.6,  # Aceita um pouco de criatividade contextual
            response_format={"type": "json_object"},
        )

        try:
            kw_payload = json.loads(result["content"])
            kw_payload["_meta"] = {
                "llm_provider": result["provider"],
                "llm_model": result["model"],
                "tokens_used": result["tokens_used"],
            }

            total_kw = len(kw_payload.get("keywords_positivas", []))
            logger.info(
                f"[{self.AGENT_NAME}] Sucesso. Extraídas {total_kw} terms "
                f"via {result['provider']}"
            )
            return kw_payload

        except json.JSONDecodeError as e:
            logger.error(f"[{self.AGENT_NAME}] Falha na Extração JSON: {e}")
            return {
                "keywords_positivas": [
                    {"termo": produto, "tipo": "BROAD", "intencao": "ALTA"}
                ],
                "keywords_negativas": ["grátis", "como fazer"],
                "bid_sugerido_brl": 1.00,
                "_meta": {
                    "llm_provider": result.get("provider", "?"),
                    "llm_model": result.get("model", "?"),
                    "erro": str(e),
                },
            }
