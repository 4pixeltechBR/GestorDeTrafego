"""
Serviço de Criação de Campanhas no Meta Ads.

Recebe os payloads JSON (do Executor Agent) e envia para a API
em 3 passos transacionais: Campaign -> Ad Set -> Ad.
"""

import logging
from typing import Dict, Any, Tuple

from app.meta.client import MetaAsyncClient, MetaAPIError
from config.meta_api import ENDPOINTS
from config.settings import settings

logger = logging.getLogger(__name__)


async def publish_campaign_structure(
    campaign_payload: Dict[str, Any],
    adset_payload: Dict[str, Any],
    ad_payload: Dict[str, Any]
) -> Tuple[bool, Dict[str, Any]]:
    """
    Publica uma campanha no Meta Ads criando os três módulos em ordem.
    Garante que se falhar no meio, a gente tem os IDs para debug/rollback.

    Args:
        campaign_payload: JSON da Campaign
        adset_payload: JSON do AdSet
        ad_payload: JSON do Ad

    Returns:
        (sucesso_boolean, dict com ids_criados ou erros)
    """
    client = MetaAsyncClient()
    result_data = {
        "campaign_id": None,
        "adset_id": None,
        "ad_id": None,
        "error": None,
        "step_failed": None
    }

    try:
        # -------------------------------------------------------------
        # PASSO 1: Criar a Campanha
        # -------------------------------------------------------------
        logger.info(f"[MetaPublish] Passo 1: Criando Campaign: '{campaign_payload.get('name')}'")
        camp_response = await client.request(
            method="POST",
            endpoint=ENDPOINTS["campaigns"],
            data=campaign_payload
        )
        result_data["campaign_id"] = camp_response.get("id")
        logger.info(f"[MetaPublish] ✅ Campaign criada com sucesso (ID: {result_data['campaign_id']})")


        # -------------------------------------------------------------
        # PASSO 2: Criar o AdSet
        # -------------------------------------------------------------
        # Injetamos o ID da campanha no payload do adset
        adset_payload["campaign_id"] = result_data["campaign_id"]

        logger.info(f"[MetaPublish] Passo 2: Criando AdSet: '{adset_payload.get('name')}'")
        adset_response = await client.request(
            method="POST",
            endpoint=ENDPOINTS["adsets"],
            data=adset_payload
        )
        result_data["adset_id"] = adset_response.get("id")
        logger.info(f"[MetaPublish] ✅ AdSet criado com sucesso (ID: {result_data['adset_id']})")


        # -------------------------------------------------------------
        # PASSO 3: Criar o Criativo (AdCreative) e o Anúncio (Ad)
        # -------------------------------------------------------------
        # O Meta exige que o anúncio "físico" seja envelopado num AdCreative antes.
        # Aqui extraímos o 'creative' do payload 'ad_payload'.
        creative_data = ad_payload.pop("creative", {})
        
        logger.info(f"[MetaPublish] Passo 3a: Criando AdCreative")
        
        # Estrutura base de um AdCreative de Link (Simplificado)
        # Em produção, usaremos object_story_spec.
        adcreative_payload = {
            "name": f"Creative - {ad_payload.get('name', 'Ad')}",
            "object_story_spec": {
                "page_id": settings.meta_page_id,
                "link_data": {
                    "link": creative_data.get("link_url", "https://exemplo.com"),
                    "message": creative_data.get("body", ""),
                    "call_to_action": {
                        "type": creative_data.get("call_to_action_type", "LEARN_MORE")
                    }
                }
            }
        }
        
        creative_resp = await client.request(
            method="POST",
            endpoint=ENDPOINTS["adcreatives"],
            data=adcreative_payload
        )
        creative_id = creative_resp.get("id")
        logger.info(f"[MetaPublish] ✅ AdCreative criado com sucesso (ID: {creative_id})")

        # Agora cria o Anúncio final (Ad) associando o AdSet e o AdCreative
        ad_payload["adset_id"] = result_data["adset_id"]
        ad_payload["creative"] = {"creative_id": creative_id}

        logger.info(f"[MetaPublish] Passo 3b: Criando Ad Final")
        ad_resp = await client.request(
            method="POST",
            endpoint=ENDPOINTS["ads"],
            data=ad_payload
        )
        result_data["ad_id"] = ad_resp.get("id")
        logger.info(f"[MetaPublish] ✅ Ad criado com sucesso (ID: {result_data['ad_id']})")


        # Finaliza com Sucesso
        return True, result_data

    except MetaAPIError as e:
        # Descobre onde falhou (se não tem campaign_id, falhou no passo 1, etc)
        if not result_data["campaign_id"]:
            result_data["step_failed"] = "CAMPAIGN"
        elif not result_data["adset_id"]:
            result_data["step_failed"] = "ADSET"
        else:
            result_data["step_failed"] = "AD"

        result_data["error"] = {
            "msg": str(e),
            "status": e.status_code,
            "meta_response": e.response
        }
        logger.error(f"[MetaPublish] ❌ Falha no passo {result_data['step_failed']}: {e.response}")
        return False, result_data
    except Exception as e:
        result_data["step_failed"] = "UNKNOWN"
        result_data["error"] = {"msg": str(e)}
        logger.error(f"[MetaPublish] ❌ Erro inesperado: {e}")
        return False, result_data
