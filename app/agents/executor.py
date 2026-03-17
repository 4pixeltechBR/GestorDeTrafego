"""
Agente Executor — Monta JSONs validados para a Meta Marketing API v25.0.

Gera os payloads dos 3 níveis: Campaign → Ad Set → Ad.
"""

import json
import logging
import uuid
from typing import Optional

from app.agents.base_agent import BaseAgent
from config.meta_api import CAMPAIGN_OBJECTIVES

logger = logging.getLogger(__name__)


class ExecutorAgent(BaseAgent):
    AGENT_ID = "executor"
    AGENT_NAME = "Executor"
    PROMPT_FILE = "executor.md"

    def _budget_to_centavos(self, budget_brl: float) -> int:
        """Converte orçamento em reais para centavos (Meta API usa centavos)."""
        return int(budget_brl * 100)

    def _validate_objective(self, objetivo: str) -> str:
        """Garante que o objetivo é válido na Meta API."""
        if objetivo in CAMPAIGN_OBJECTIVES:
            return objetivo
        logger.warning(
            f"[{self.AGENT_NAME}] Objetivo inválido '{objetivo}'. "
            f"Usando OUTCOME_TRAFFIC como padrão."
        )
        return "OUTCOME_TRAFFIC"

    async def build_campaign_json(
        self,
        produto: str,
        nicho: str,
        copy: dict,
        orcamento_diario: float,
        publico_alvo: dict,
        objetivo: str = "OUTCOME_TRAFFIC",
        nome_campanha: Optional[str] = None,
        link_destino: str = "https://exemplo.com.br",
        campaign_id: Optional[str] = None,
        canal: str = "meta",
        keywords_payload: Optional[dict] = None
    ) -> dict:
        """
        Monta os 3 JSONs da Meta API (Campaign, Ad Set, Ad).

        Args:
            produto: Nome do produto/serviço
            nicho: Nicho do negócio
            copy: Dict com titulo, texto_principal, descricao, cta
            orcamento_diario: Orçamento em reais (ex: 30.00)
            publico_alvo: Dict com segmentação
            objetivo: Objetivo da campanha Meta
            nome_campanha: Nome personalizado (gerado automaticamente se None)
            link_destino: URL de destino do anúncio
            campaign_id: ID interno (para audit log)

        Returns:
            dict com campaign, adset e ad JSONs prontos para a Meta API
        """
        objetivo_validado = self._validate_objective(objetivo)
        budget_centavos = self._budget_to_centavos(orcamento_diario)

        # Contexto estruturado para o Executor (mais preciso = menos tokens)
        context = f"""
DADOS DA CAMPANHA:
- Produto: {produto}
- Nicho: {nicho}
- Objetivo Meta API: {objetivo_validado}
- Orçamento diário: R${orcamento_diario:.2f} = {budget_centavos} centavos
- Link de destino: {link_destino}

COPY SELECIONADA:
- Título: {copy.get('titulo', '')}
- Texto principal: {copy.get('texto_principal', '')}
- Descrição: {copy.get('descricao', '')}
- CTA: {copy.get('cta', 'LEARN_MORE')}

PÚBLICO-ALVO:
- Faixa etária: {publico_alvo.get('idade_min', 25)}-{publico_alvo.get('idade_max', 55)} anos
- Interesses: {publico_alvo.get('interesses', [])}
- Localização: {publico_alvo.get('localizacao', 'Brasil')}
"""

        if canal == "google_search":
            user_message = (
                "Monte o payload JSON para o motor gRPC do Google Ads.\n"
                "Deve conter os nós: 'budget', 'campaign', 'ad_group', 'keywords' (array de strings extraídos do keywords_payload que recebi no dict keywords), e 'ad'.\n"
                "O 'ad' deve conter 'headlines', 'descriptions' e 'final_urls'.\n"
                "Para 'campaign', o status deve ser 'PAUSED'."
            )
            # Injeta as KWs no context
            context += f"\nKEYWORDS: {json.dumps(keywords_payload) if keywords_payload else '[]'}"
        else:
            user_message = (
                "Monte os 3 JSONs para a Meta Marketing API v25.0:\n"
                "1. Campaign\n2. Ad Set\n3. Ad\n\n"
                "REGRAS CRÍTICAS:\n"
                "- Status sempre 'PAUSED' (nunca ACTIVE)\n"
                "- Budget em CENTAVOS\n"
                "- Retorne apenas JSON válido"
            )

        result = await self.think(
            user_message=user_message,
            context=context,
            temperature=0.1,  # Mínimo — zero criatividade, máxima precisão
            response_format={"type": "json_object"},
        )

        try:
            payload = json.loads(result["content"])

            # Injeção de segurança: garante PAUSED em todos os níveis
            for key in ["campaign", "adset", "ad"]:
                if key in payload:
                    payload[key]["status"] = "PAUSED"

            # Injeção de ID de rastreamento interno
            internal_id = campaign_id or str(uuid.uuid4())[:8]
            if "campaign" in payload:
                campaign_name = payload["campaign"].get("name", "")
                if not campaign_name or campaign_name == "{PENDENTE}":
                    payload["campaign"]["name"] = (
                        nome_campanha or f"[GTrafego] {produto[:30]} #{internal_id}"
                    )

            payload["_meta"] = {
                "llm_provider": result["provider"],
                "llm_model": result["model"],
                "tokens_used": result["tokens_used"],
                "orcamento_original_brl": orcamento_diario,
                "budget_centavos": budget_centavos,
            }

            logger.info(
                f"[{self.AGENT_NAME}] JSONs montados para '{produto}' "
                f"via {result['provider']} ({result['tokens_used']['total']} tokens)"
            )
            return payload

        except json.JSONDecodeError as e:
            logger.error(f"[{self.AGENT_NAME}] Erro ao parsear JSON: {e}")
            return {
                "erro": str(e),
                "raw_response": result["content"][:500],
                "_meta": {
                    "llm_provider": result.get("provider", "?"),
                    "llm_model": result.get("model", "?"),
                },
            }
