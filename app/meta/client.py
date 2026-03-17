"""
Meta API Client — Cliente assíncrono para a Graph API v25.0.

Lida com autenticação, limites de taxa (rate limits) e 
erros da API de forma centralizada.
"""

import httpx
import logging
import asyncio
from typing import Any, Dict, Optional

from config.settings import settings
from config.meta_api import META_GRAPH_URL

logger = logging.getLogger(__name__)


class MetaAPIError(Exception):
    """Exceção customizada para erros da Meta API."""
    def __init__(self, message: str, status_code: int = 500, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class MetaAsyncClient:
    """
    Cliente assíncrono para interagir com a Meta Marketing API.
    Gerencia o access_token, o ad_account_id e trata o Rate Limiting.
    """

    def __init__(self):
        self.access_token = settings.meta_access_token
        self.ad_account_id = settings.meta_ad_account_id
        
        # O ID da conta de anúncio no Meta sempre começa com 'act_'
        # Se o usuário não colocou, a gente corrige automaticamente.
        if self.ad_account_id and not self.ad_account_id.startswith("act_"):
            self.ad_account_id = f"act_{self.ad_account_id}"

        self.base_url = META_GRAPH_URL

    @property
    def is_configured(self) -> bool:
        """Verifica se as credenciais essenciais estão presentes."""
        return bool(self.access_token and self.ad_account_id)

    def _build_url(self, endpoint: str) -> str:
        """Constrói a URL completa substituindo {ad_account_id}."""
        if "{ad_account_id}" in endpoint:
            path = endpoint.replace("{ad_account_id}", self.ad_account_id)
        else:
            path = endpoint
            
        # Garante que o path comece com /
        if not path.startswith("/"):
            path = f"/{path}"
            
        return f"{self.base_url}{path}"

    async def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Verifica erros e formata a resposta."""
        try:
            data = response.json()
        except Exception:
            data = {"error": {"message": "Invalid JSON response"}}

        if response.status_code >= 400:
            error_data = data.get("error", {})
            message = error_data.get("message", "Erro desconhecido")
            code = error_data.get("code", 0)
            
            # Rate limit do Meta Ads (Código 17)
            if code == 17:
                logger.warning(f"[MetaAPI] Rate limit atingido. Aguardando...")
                # O ideal seria ler o header 'x-business-use-case-usage'
                raise MetaAPIError(f"Rate Limit Meta API: {message}", response.status_code, error_data)

            logger.error(f"[MetaAPI] Erro {response.status_code}: {message} | Code: {code}")
            raise MetaAPIError(message, response.status_code, error_data)

        return data

    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        retries: int = 3
    ) -> Dict[str, Any]:
        """
        Executa a requisição REST HTTP assíncrona.
        Possui retry automático para timeouts.
        """
        if not self.is_configured:
            raise MetaAPIError("Credenciais do Meta Ads não configuradas no .env", 401)

        url = self._build_url(endpoint)
        
        _params = params or {}
        _params["access_token"] = self.access_token
        
        attempt = 0
        while attempt < retries:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    if method.upper() == "GET":
                        response = await client.get(url, params=_params)
                    elif method.upper() == "POST":
                        response = await client.post(url, params=_params, json=data)
                    else:
                        raise ValueError(f"Método HTTP não suportado: {method}")
                    
                    return await self._handle_response(response)

            except (httpx.TimeoutException, httpx.NetworkError) as e:
                attempt += 1
                logger.warning(f"[MetaAPI] Falha de rede ({attempt}/{retries}): {e}")
                if attempt >= retries:
                    raise MetaAPIError(f"Falha de conexão com a Meta API após {retries} tentativas.", 503)
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except MetaAPIError as e:
                # Se for Rate Limit (17), tenta esperar e repetir
                if e.response and e.response.get("code") == 17 and attempt < retries:
                    attempt += 1
                    wait_time = 10 * attempt
                    logger.warning(f"[MetaAPI] Aplicando backoff para Rate Limit: esperando {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                # Outros erros da API (dados inválidos, auth error) são repassados imediatamente
                raise
