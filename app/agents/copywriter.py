"""
Agente Copywriter — Gerador de texts persuasivos para Meta Ads.

Cria múltiplas opções de copy (A/B test ready) adaptadas ao nicho.
"""

import json
import logging
import yaml
from pathlib import Path
from typing import Optional

from app.agents.base_agent import BaseAgent
from config.settings import BASE_DIR

logger = logging.getLogger(__name__)


class CopywriterAgent(BaseAgent):
    AGENT_ID = "copywriter"
    AGENT_NAME = "Copywriter"
    PROMPT_FILE = "copywriter.md"

    def _load_niche_template(self, niche: str) -> Optional[dict]:
        """Carrega template YAML do nicho para enriquecer o contexto."""
        template_path = BASE_DIR / "templates" / "nichos" / f"{niche}.yaml"
        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                logger.info(
                    f"[{self.AGENT_NAME}] Template de nicho carregado: {niche}"
                )
                return data
        logger.warning(
            f"[{self.AGENT_NAME}] Template não encontrado para nicho: {niche}"
        )
        return None

    async def generate_copies(
        self,
        produto: str,
        nicho: str,
        publico_alvo: dict,
        objetivo: str = "OUTCOME_TRAFFIC",
        contexto_extra: Optional[str] = None,
        campaign_id: Optional[str] = None,
    ) -> dict:
        """
        Gera 2-3 opções de copy para Meta Ads.

        Args:
            produto: Produto/serviço a anunciar
            nicho: Nicho do negócio (ex: "auto_center")
            publico_alvo: Dict com dados do público
            objetivo: Objetivo da campanha Meta
            contexto_extra: Informações adicionais (ex: promoção especial)
            campaign_id: ID da campanha (para audit log)

        Returns:
            dict com lista de opções de copy validadas
        """
        # Carrega template do nicho para contexto
        template = self._load_niche_template(nicho)
        context_parts = []

        if template:
            diretrizes = template.get("copy_diretrizes", {})
            benchmarks = template.get("benchmarks", {})
            context_parts.append(
                f"NICHO: {template.get('nome_display', nicho)}\n"
                f"TOM DE VOZ: {diretrizes.get('tom', 'profissional')}\n"
                f"GATILHOS EFICAZES: {', '.join(diretrizes.get('gatilhos', []))}\n"
                f"PROIBIDO: {', '.join(diretrizes.get('proibido', []))}\n"
                f"CPC médio do nicho: R${benchmarks.get('cpc_medio', '?')}\n"
            )

        if publico_alvo:
            context_parts.append(
                f"PÚBLICO-ALVO:\n"
                f"  Faixa etária: {publico_alvo.get('idade_min', 18)}-"
                f"{publico_alvo.get('idade_max', 65)} anos\n"
                f"  Interesses: {', '.join(publico_alvo.get('interesses', []))}\n"
                f"  Localização: {publico_alvo.get('localizacao', 'Brasil')}\n"
            )

        if contexto_extra:
            context_parts.append(f"CONTEXTO ADICIONAL: {contexto_extra}")

        context = "\n".join(context_parts) if context_parts else None

        result = await self.think(
            user_message=(
                f"Crie 2-3 opções de copy para este anúncio no Meta Ads:\n\n"
                f"PRODUTO/SERVIÇO: {produto}\n"
                f"OBJETIVO DA CAMPANHA: {objetivo}\n\n"
                f"Gere copies prontas para teste A/B. Inclua título, "
                f"texto principal, descrição e CTA para cada opção."
            ),
            context=context,
            temperature=0.8,  # Alto — queremos criatividade
            response_format={"type": "json_object"},
        )

        try:
            copies = json.loads(result["content"])

            # Garante que o campo "opcoes" existe
            if "opcoes" not in copies:
                # Tenta normalizar se o LLM usou estrutura diferente
                if isinstance(copies, list):
                    copies = {"opcoes": copies}
                else:
                    copies = {"opcoes": [copies]}

            copies["_meta"] = {
                "llm_provider": result["provider"],
                "llm_model": result["model"],
                "tokens_used": result["tokens_used"],
                "nicho": nicho,
                "produto": produto,
            }

            num_opcoes = len(copies.get("opcoes", []))
            logger.info(
                f"[{self.AGENT_NAME}] {num_opcoes} copies geradas para '{produto}' "
                f"via {result['provider']}"
            )
            return copies

        except json.JSONDecodeError as e:
            logger.error(f"[{self.AGENT_NAME}] Erro ao parsear JSON: {e}")
            # Retorna copy de fallback básica
            return {
                "opcoes": [
                    {
                        "titulo": produto[:40],
                        "texto_principal": f"Conheça nosso {produto}. Entre em contato!",
                        "descricao": "Saiba mais",
                        "cta": "LEARN_MORE",
                    }
                ],
                "_meta": {
                    "llm_provider": result.get("provider", "?"),
                    "llm_model": result.get("model", "?"),
                    "erro": str(e),
                },
            }
