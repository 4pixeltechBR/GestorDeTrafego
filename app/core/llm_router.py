"""
LLM Router — Cascata inteligente de APIs de IA.

Lê a configuração do llm_cascade.yaml e tenta cada provedor
em sequência até obter uma resposta válida.
"""

import logging
import yaml
from pathlib import Path
from typing import Optional

import litellm

from config.settings import settings, BASE_DIR

logger = logging.getLogger(__name__)

# Desabilita logs verbosos do LiteLLM
litellm.suppress_debug_info = True


def _load_cascade_config() -> dict:
    """Carrega configuração de cascata do YAML."""
    config_path = BASE_DIR / "config" / "llm_cascade.yaml"
    if not config_path.exists():
        raise FileNotFoundError(
            f"Arquivo de cascata não encontrado: {config_path}\n"
            "Verifique se config/llm_cascade.yaml existe."
        )
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# Cache da configuração
_cascade_config: Optional[dict] = None


def get_cascade_config() -> dict:
    """Retorna configuração de cascata (singleton com cache)."""
    global _cascade_config
    if _cascade_config is None:
        _cascade_config = _load_cascade_config()
    return _cascade_config


def _get_api_key(provider: str) -> Optional[str]:
    """Mapeia provedor para a chave de API correspondente."""
    key_map = {
        "groq": settings.groq_api_key,
        "google": settings.google_ai_key,
        "nvidia_nim": settings.nvidia_nim_key,
        "openrouter": settings.openrouter_key,
    }
    return key_map.get(provider)


async def call_llm(
    agent_name: str,
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    response_format: Optional[dict] = None,
) -> dict:
    """
    Chama um LLM usando a cascata configurada para o agente.

    Tenta cada modelo da lista em sequência. Se um falhar
    (rate limit, timeout, erro), pula para o próximo.

    Args:
        agent_name: Nome do agente (ex: "orchestrator", "copywriter")
        messages: Lista de mensagens no formato OpenAI
        temperature: Criatividade (0.0 = preciso, 1.0 = criativo)
        max_tokens: Limite de tokens na resposta
        response_format: Formato de resposta (ex: {"type": "json_object"})

    Returns:
        dict com keys: "content", "model", "provider", "tokens_used"

    Raises:
        RuntimeError: Se todos os provedores falharem.
    """
    config = get_cascade_config()
    agent_config = config.get(agent_name)

    if not agent_config:
        raise ValueError(
            f"Agente '{agent_name}' não encontrado em llm_cascade.yaml.\n"
            f"Agentes disponíveis: {list(config.keys())}"
        )

    models = agent_config.get("models", [])
    errors = []

    for model_cfg in models:
        provider = model_cfg["provider"]
        model_name = model_cfg["model"]
        model_max_tokens = max_tokens or model_cfg.get("max_tokens", 2048)

        # Verifica se a API Key está configurada
        api_key = _get_api_key(provider)
        if not api_key:
            logger.debug(
                f"[{agent_name}] Pulando {provider}/{model_name} "
                f"(API Key não configurada)"
            )
            continue

        try:
            logger.info(
                f"[{agent_name}] Tentando: {provider}/{model_name}"
            )

            kwargs = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": model_max_tokens,
                "api_key": api_key,
            }

            if response_format:
                kwargs["response_format"] = response_format

            response = await litellm.acompletion(**kwargs)

            content = response.choices[0].message.content
            usage = response.usage

            result = {
                "content": content,
                "model": model_name,
                "provider": provider,
                "tokens_used": {
                    "prompt": usage.prompt_tokens,
                    "completion": usage.completion_tokens,
                    "total": usage.total_tokens,
                },
            }

            logger.info(
                f"[{agent_name}] ✅ Sucesso via {provider}/{model_name} "
                f"({usage.total_tokens} tokens)"
            )

            return result

        except Exception as e:
            error_msg = f"{provider}/{model_name}: {type(e).__name__}: {e}"
            errors.append(error_msg)
            logger.warning(
                f"[{agent_name}] ⚠️ Falha em {error_msg}. "
                f"Tentando próximo..."
            )
            continue

    # Todos os provedores falharam
    error_detail = "\n".join(f"  - {err}" for err in errors)
    raise RuntimeError(
        f"[{agent_name}] ❌ Todos os provedores falharam!\n"
        f"Erros:\n{error_detail}\n\n"
        f"Verifique:\n"
        f"  1. Se pelo menos uma API Key está configurada no .env\n"
        f"  2. Se as chaves não expiraram\n"
        f"  3. Se você não excedeu os limites de cota"
    )
