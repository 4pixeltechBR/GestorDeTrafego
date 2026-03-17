"""
Configurações centrais do Gestor de Tráfego IA.
Carrega variáveis do .env e expõe como objeto tipado.
"""

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


# Raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Configurações carregadas do .env com validação Pydantic."""

    # --- App ---
    app_name: str = Field(default="GestorDeTrafego")
    port: int = Field(default=8080)
    log_level: str = Field(default="INFO")

    # --- APIs de IA ---
    groq_api_key: Optional[str] = Field(default=None)
    google_ai_key: Optional[str] = Field(default=None)
    nvidia_nim_key: Optional[str] = Field(default=None)
    openrouter_key: Optional[str] = Field(default=None)

    # --- Meta Ads ---
    meta_app_id: Optional[str] = Field(default=None)
    meta_app_secret: Optional[str] = Field(default=None)
    meta_access_token: Optional[str] = Field(default=None)
    meta_ad_account_id: Optional[str] = Field(default=None)

    # --- Google Ads ---
    google_ads_developer_token: Optional[str] = Field(default=None)
    google_ads_client_id: Optional[str] = Field(default=None)
    google_ads_client_secret: Optional[str] = Field(default=None)
    google_ads_refresh_token: Optional[str] = Field(default=None)
    google_ads_customer_id: Optional[str] = Field(default=None)  # Sem hífens (ex: 1234567890)
    google_ads_login_customer_id: Optional[str] = Field(default=None)

    # --- Telegram ---
    telegram_bot_token: Optional[str] = Field(default=None)
    telegram_admin_chat_id: Optional[str] = Field(default=None)

    # --- Guardrails ---
    budget_max_diario: float = Field(default=100.0)
    budget_max_mensal: float = Field(default=3000.0)
    approval_mode: str = Field(default="copilot")  # "copilot" ou "auto"

    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    @property
    def available_providers(self) -> list[str]:
        """Retorna lista de provedores de IA configurados."""
        providers = []
        if self.groq_api_key:
            providers.append("groq")
        if self.google_ai_key:
            providers.append("google")
        if self.nvidia_nim_key:
            providers.append("nvidia_nim")
        if self.openrouter_key:
            providers.append("openrouter")
        return providers

    @property
    def has_meta_config(self) -> bool:
        """Verifica se Meta Ads está configurado."""
        return all([
            self.meta_app_id,
            self.meta_access_token,
            self.meta_ad_account_id,
        ])

    @property
    def has_telegram(self) -> bool:
        """Verifica se Telegram está configurado."""
        return all([
            self.telegram_bot_token,
            self.telegram_admin_chat_id,
        ])

    @property
    def has_google_ads(self) -> bool:
        """Verifica se Google Ads está configurado."""
        return all([
            self.google_ads_developer_token,
            self.google_ads_client_id,
            self.google_ads_client_secret,
            self.google_ads_refresh_token,
            self.google_ads_customer_id,
        ])


# Instância global (singleton)
settings = Settings()
