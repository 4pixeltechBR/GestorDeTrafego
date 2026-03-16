"""
Agente Compliance — Valida copies contra políticas do Meta Ads.

Classifica risco, aponta problemas e sugere correções.
"""

import json
import logging
from typing import Optional

from app.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

# Categorias de risco alto (sempre bloquear)
HIGH_RISK_TERMS = [
    "garantido", "100% garantido", "cure", "cura milagrosa",
    "enriqueça", "ganhe dinheiro fácil", "sem esforço",
    "resultados imediatos", "comprovado cientificamente",
    "clique aqui", "URGENTE", "GRÁTIS AGORA",
]


class ComplianceAgent(BaseAgent):
    AGENT_ID = "compliance"
    AGENT_NAME = "Compliance"
    PROMPT_FILE = "compliance.md"

    def _pre_check(self, copy_text: str) -> list[dict]:
        """
        Verificação local rápida (sem LLM) de termos de alto risco.
        Evita gastar tokens em casos óbvios.
        """
        problems = []
        text_lower = copy_text.lower()
        for term in HIGH_RISK_TERMS:
            if term.lower() in text_lower:
                problems.append({
                    "tipo": "PRE_CHECK_LOCAL",
                    "trecho": term,
                    "sugestao": f"Remova ou substitua '{term}'",
                })
        return problems

    async def validate_copy(
        self,
        copy_options: list[dict],
        nicho: str = "servicos",
        campaign_id: Optional[str] = None,
    ) -> dict:
        """
        Valida uma lista de copies contra as políticas do Meta Ads.

        Args:
            copy_options: Lista de dicts com titulo, texto_principal, etc.
            nicho: Nicho para contextualizar limites aceitáveis
            campaign_id: ID da campanha (para audit log)

        Returns:
            dict com copies aprovadas, rejeitadas e sugestões de correção
        """
        # Pre-check local em todas as copies (rápido, sem LLM)
        pre_issues = []
        for i, copy in enumerate(copy_options):
            full_text = f"{copy.get('titulo', '')} {copy.get('texto_principal', '')} {copy.get('descricao', '')}"
            issues = self._pre_check(full_text)
            if issues:
                pre_issues.append({"opcao": i, "problemas": issues})

        # Formata as copies para o LLM avaliar
        copies_formatted = json.dumps(copy_options, ensure_ascii=False, indent=2)
        pre_issues_formatted = (
            json.dumps(pre_issues, ensure_ascii=False) if pre_issues
            else "Nenhum problema detectado no pre-check local."
        )

        result = await self.think(
            user_message=(
                f"Valide estas copies de anúncio contra as políticas do Meta Ads:\n\n"
                f"NICHO: {nicho}\n\n"
                f"COPIES:\n{copies_formatted}\n\n"
                f"PRE-CHECK LOCAL IDENTIFICOU:\n{pre_issues_formatted}\n\n"
                f"Analise cada opção e retorne um JSON com aprovadas, "
                f"rejeitadas e sugestões de correção."
            ),
            temperature=0.1,  # Mínimo — queremos rigor, não criatividade
            response_format={"type": "json_object"},
        )

        try:
            validation = json.loads(result["content"])
            validation["_meta"] = {
                "llm_provider": result["provider"],
                "llm_model": result["model"],
                "tokens_used": result["tokens_used"],
                "pre_check_issues": pre_issues,
            }

            risco = validation.get("risco", "DESCONHECIDO")
            aprovado = validation.get("aprovado", False)
            logger.info(
                f"[{self.AGENT_NAME}] Resultado: {'✅ APROVADO' if aprovado else '❌ REJEITADO'} "
                f"| Risco: {risco} | via {result['provider']}"
            )
            return validation

        except json.JSONDecodeError as e:
            logger.error(f"[{self.AGENT_NAME}] Erro ao parsear resposta: {e}")
            # Em caso de erro, bloqueia por segurança
            return {
                "aprovado": False,
                "risco": "ALTO",
                "problemas": [
                    {
                        "tipo": "ERRO_SISTEMA",
                        "trecho": "N/A",
                        "sugestao": "Revisão manual necessária.",
                    }
                ],
                "special_ad_categories": [],
                "observacoes": f"Erro ao processar resposta do Compliance: {e}",
                "_meta": {
                    "llm_provider": result.get("provider", "?"),
                    "llm_model": result.get("model", "?"),
                    "erro": str(e),
                },
            }
