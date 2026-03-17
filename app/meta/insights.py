"""
Serviço de Insights do Meta Ads.

Busca métricas e KPIs diários das campanhas ativas para
alimentar o agente Analista.
"""

import logging
from typing import Dict, Any, List

from app.meta.client import MetaAsyncClient, MetaAPIError
from config.meta_api import ENDPOINTS, INSIGHT_FIELDS

logger = logging.getLogger(__name__)


async def fetch_campaign_metrics(campaign_meta_id: str, date_preset: str = "last_7d") -> Dict[str, Any]:
    """
    Busca os insights agregados de uma campanha específica.

    Args:
        campaign_meta_id: O ID Real da campanha dentro do Facebook/Meta
        date_preset: Período (ex: "today", "yesterday", "last_7d", "last_30d")

    Returns:
        Um dicionário contendo as métricas formatadas e convertidas para Float/Int
    """
    client = MetaAsyncClient()
    endpoint = ENDPOINTS["insights"].replace("{object_id}", campaign_meta_id)
    
    params = {
        "fields": ",".join(INSIGHT_FIELDS),
        "date_preset": date_preset,
        "level": "campaign"
    }

    try:
        response = await client.request("GET", endpoint, params=params)
        
        # A Meta API retorna um array "data"
        data = response.get("data", [])
        
        if not data:
            logger.info(f"[MetaInsights] Sem dados para a campanha {campaign_meta_id} no período {date_preset}")
            return _empty_metrics()

        # Pega a linha agregada
        raw_metrics = data[0]

        # Converte as strings da Meta API para números Python
        metrics = {
            "spend": float(raw_metrics.get("spend", 0.0)),
            "impressions": int(raw_metrics.get("impressions", 0)),
            "clicks": int(raw_metrics.get("clicks", 0)),
            "cpc": float(raw_metrics.get("cpc", 0.0)),
            "ctr": float(raw_metrics.get("ctr", 0.0)),
            "cpm": float(raw_metrics.get("cpm", 0.0)),
            "frequency": float(raw_metrics.get("frequency", 1.0)),
            
            # Eventos complexos (Ações e ROAS) exigem iteração no array
            "conversions": _extract_action(raw_metrics, action_type="omni_purchase"),
            "roas": _extract_roas(raw_metrics)
        }
        
        return metrics

    except MetaAPIError as e:
        logger.error(f"[MetaInsights] Erro ao buscar métricas da proc {campaign_meta_id}: {e}")
        return _empty_metrics()
    except Exception as e:
        logger.error(f"[MetaInsights] Falha inesperada buscando métricas: {e}")
        return _empty_metrics()


def _empty_metrics() -> Dict[str, Any]:
    """Retorna um stub zerado."""
    return {
        "spend": 0.0,
        "impressions": 0,
        "clicks": 0,
        "cpc": 0.0,
        "ctr": 0.0,
        "cpm": 0.0,
        "frequency": 0.0,
        "conversions": 0,
        "roas": 0.0
    }


def _extract_action(raw_data: Dict[str, Any], action_type: str = "omni_purchase") -> int:
    """Extrai resultados (ex: conversões, leads) da lista de 'actions' da Meta."""
    actions = raw_data.get("actions", [])
    for act in actions:
        if act.get("action_type") == action_type:
            return int(act.get("value", 0))
    return 0


def _extract_roas(raw_data: Dict[str, Any]) -> float:
    """Extrai o retorno sobre investimento (ROAS)."""
    roas_list = raw_data.get("purchase_roas", [])
    for roas_entry in roas_list:
        if roas_entry.get("action_type") == "omni_purchase":
            return float(roas_entry.get("value", 0.0))
    return 0.0
