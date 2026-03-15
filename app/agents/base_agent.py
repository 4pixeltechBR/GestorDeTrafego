"""
Base Agent — Classe base para todos os agentes do sistema.

Fornece:
- Integração com o LLM Router (cascata automática)
- Logging estruturado
- Registro de ações no Audit Log
- Carregamento de System Prompts de arquivo
"""

import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from app.core.llm_router import call_llm
from app.core.database import get_db
from config.settings import BASE_DIR

logger = logging.getLogger(__name__)


class BaseAgent:
    """Classe base para agentes especializados."""

    # Sobrescrever nas subclasses
    AGENT_ID: str = "base"
    AGENT_NAME: str = "Base Agent"
    PROMPT_FILE: str = ""  # ex: "orchestrator.md"

    def __init__(self):
        self._system_prompt: Optional[str] = None

    @property
    def system_prompt(self) -> str:
        """Carrega o System Prompt do arquivo .md correspondente."""
        if self._system_prompt is None:
            prompt_path = BASE_DIR / "templates" / "prompts" / self.PROMPT_FILE
            if prompt_path.exists():
                self._system_prompt = prompt_path.read_text(encoding="utf-8")
                logger.debug(
                    f"[{self.AGENT_NAME}] System Prompt carregado: "
                    f"{self.PROMPT_FILE}"
                )
            else:
                self._system_prompt = (
                    f"Você é o {self.AGENT_NAME}, um agente especializado "
                    f"do sistema Gestor de Tráfego IA."
                )
                logger.warning(
                    f"[{self.AGENT_NAME}] Prompt não encontrado: "
                    f"{prompt_path}. Usando prompt genérico."
                )
        return self._system_prompt

    async def think(
        self,
        user_message: str,
        context: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[dict] = None,
    ) -> dict:
        """
        Envia uma mensagem ao LLM usando a cascata configurada.

        Args:
            user_message: A mensagem/instrução para o agente
            context: Contexto adicional (ex: dados de campanha)
            temperature: Criatividade (0.0-1.0)
            max_tokens: Limite de tokens
            response_format: Formato esperado (ex: JSON)

        Returns:
            dict: {"content": str, "model": str, "provider": str, "tokens_used": dict}
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
        ]

        if context:
            messages.append({
                "role": "user",
                "content": f"[CONTEXTO]\n{context}",
            })

        messages.append({
            "role": "user",
            "content": user_message,
        })

        result = await call_llm(
            agent_name=self.AGENT_ID,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
        )

        # Registra no Audit Log
        await self._log_action(
            action="think",
            input_summary=user_message[:200],
            output_summary=result["content"][:200],
            llm_provider=result["provider"],
            llm_model=result["model"],
            tokens_used=result["tokens_used"]["total"],
        )

        return result

    async def _log_action(
        self,
        action: str,
        input_summary: str = "",
        output_summary: str = "",
        campaign_id: Optional[str] = None,
        llm_provider: str = "",
        llm_model: str = "",
        tokens_used: int = 0,
        success: bool = True,
    ) -> None:
        """Registra uma ação no Audit Log (SQLite)."""
        try:
            db = await get_db()
            await db.execute(
                """
                INSERT INTO audit_log
                (agent, action, campaign_id, input_summary,
                 output_summary, llm_provider, llm_model,
                 tokens_used, success)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.AGENT_ID,
                    action,
                    campaign_id,
                    input_summary,
                    output_summary,
                    llm_provider,
                    llm_model,
                    tokens_used,
                    1 if success else 0,
                ),
            )
            await db.commit()
            await db.close()
        except Exception as e:
            logger.error(f"[{self.AGENT_NAME}] Erro ao registrar audit: {e}")
