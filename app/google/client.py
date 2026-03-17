"""
Cliente Assíncrono para o Google Ads API (gRPC).

Diferente do Meta (que usamos httpx para REST puro), 
o Google Ads exige Protocol Buffers (gRPC) através da biblioteca oficial.
"""

import logging
from typing import Optional
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

from config.settings import settings
from config.google_ads import GOOGLE_ADS_API_VERSION

logger = logging.getLogger(__name__)

class GoogleAdsAsyncClient:
    """Wrapper para a API do Google Ads"""

    def __init__(self):
        self._client: Optional[GoogleAdsClient] = None
        self._customer_id: Optional[str] = settings.google_ads_customer_id

    @property
    def client(self) -> GoogleAdsClient:
        """Inicializa (lazy load) e retorna a instância do cliente."""
        if self._client is None:
            if not settings.has_google_ads:
                raise ValueError("Credenciais do Google Ads ausentes no .env.")

            credentials = {
                "developer_token": settings.google_ads_developer_token,
                "client_id": settings.google_ads_client_id,
                "client_secret": settings.google_ads_client_secret,
                "refresh_token": settings.google_ads_refresh_token,
                "use_proto_plus": True
            }
            
            if settings.google_ads_login_customer_id:
                credentials["login_customer_id"] = settings.google_ads_login_customer_id

            try:
                self._client = GoogleAdsClient.load_from_dict(
                    credentials, 
                    version=GOOGLE_ADS_API_VERSION
                )
                logger.info("[GoogleAds] Cliente gRPC inicializado com sucesso.")
            except Exception as e:
                logger.error(f"[GoogleAds] Erro crítico ao iniciar SDK: {e}")
                raise

        return self._client

    def get_service(self, service_name: str):
        """
        Retorna um serviço gRPC do Google Ads.
        Exemplo: 'CampaignService', 'AdGroupService'
        """
        return self.client.get_service(service_name)

    @property
    def customer_id(self) -> str:
        """Retorna o ID da conta do Google (sem hífens)."""
        if not self._customer_id:
            raise ValueError("GOOGLE_ADS_CUSTOMER_ID não configurado.")
        return self._customer_id.replace("-", "")

    def handle_grpc_error(self, exception: GoogleAdsException) -> dict:
        """Parseia erros gigantescos do gRPC em dicts legíveis."""
        errors = []
        for error in exception.failure.errors:
            errors.append({
                "message": error.message,
                "error_code": str(error.error_code),
                "trigger": error.trigger.string_value if error.trigger else None
            })
            
        logger.error(f"[GoogleAds] 🚫 Falha gRPC. {len(errors)} erros.")
        for err in errors:
            logger.error(f"  → Code: {err['error_code']} | Msg: {err['message']} | Trigger: {err['trigger']}")
            
        return {"status": "error", "grpc_errors": errors}

# Instância Singleton
google_client = GoogleAdsAsyncClient()
