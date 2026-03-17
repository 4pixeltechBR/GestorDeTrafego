"""
Leitor de Insights (Métricas) do Google Ads.

Busca dados de anúncios executando instruções GAQL via serviço `GoogleAdsService`.
"""

import logging
from typing import List, Dict

from app.google.client import google_client
from config.google_ads import GAQL_CAMPAIGN_METRICS, MICROS_MULTIPLIER

logger = logging.getLogger(__name__)

async def fetch_google_metrics(date_range: str = "LAST_7_DAYS") -> List[Dict]:
    """
    Simula e processa a busca de métricas usando a GAQL query definida nas constantes.
    """
    logger.info(f"[GoogleAds] Lendo Métricas GAQL para: {date_range}...")
    
    # 1. Carrega o cliente
    try:
        client = google_client.client
        customer_id = google_client.customer_id
        ga_service = client.get_service("GoogleAdsService")
    except ValueError as e:
        logger.error(str(e))
        return []

    query = GAQL_CAMPAIGN_METRICS.format(date_range=date_range)
    
    # 2. Executa Query nativa. Simulando porque developer_token ausente no momento:
    # response = ga_service.search_stream(customer_id=customer_id, query=query)
    # results = []
    # for batch in response:
    #     for row in batch.results:
    #         results.append({...})
            
    logger.info("[GoogleAds] Execução GAQL retornou mock de 1 campanha.")
    return [
        {
            "ad_account_id": customer_id,
            "campaign_id": "google_123",
            "campaign_name": "Campanha Mock Google Search",
            "status": "PAUSED",
            "spend": 50.0, # Convertido do micros / MICROS_MULTIPLIER
            "impressions": 1500,
            "clicks": 150,
            "cpc": 0.33,
            "ctr": 10.0,
            "cpm": 33.0,
            "actions": 15,
            "cost_per_action_type": 3.33,
            "purchase_roas": 0.0, # Precisa tag globalsite do google
        }
    ]
