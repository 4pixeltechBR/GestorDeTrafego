"""
Rotas REST (FastAPI) para comunicação frontend-backend.
"""

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.core.database import get_db
from app.agents.orchestrator import OrchestratorAgent
from app.agents.copywriter import CopywriterAgent
from app.agents.compliance import ComplianceAgent
from app.agents.executor import ExecutorAgent
from app.meta.manager import publish_campaign_structure
from app.guardrails.budget import check_budget_guardrails, BudgetExceededError

logger = logging.getLogger(__name__)

router = APIRouter()

class BriefingRequest(BaseModel):
    briefing: str

@router.post("/campaigns/setup")
async def setup_campaign(request: BriefingRequest, background_tasks: BackgroundTasks):
    """
    Recebe um briefing do frontend (texto livre) e aciona a cascata de IA.
    Para não prender o Frontend, em produção isso deveria ser via WebSocket
    ou Background Task. Aqui faremos de forma síncrona/simplificada,
    pois os llm_routers respondem rápido pela ordem prioritária do yaml.
    """
    if not request.briefing or len(request.briefing) < 10:
        raise HTTPException(status_code=400, detail="Briefing muito curto. Explique melhor seu objetivo.")

    try:
        logger.info(f"🚀 Iniciando Geração Inteligente. Briefing: {request.briefing[:50]}...")
        
        # 1. Orquestrador
        orchestrator = OrchestratorAgent()
        orch_res = await orchestrator.parse_briefing(request.briefing)
        orcamento = orch_res.get("orcamento_diario", 50.0)

        # 2. Guardrails Verificação Previa (Evita gastar token se já não pode processar o orçamento)
        try:
            await check_budget_guardrails(orcamento)
        except BudgetExceededError as e:
            raise HTTPException(status_code=403, detail=str(e))

        # 3. Copywriter
        copywriter = CopywriterAgent()
        copies = await copywriter.generate_copies(
            produto=orch_res.get("produto"),
            nicho=orch_res.get("nicho"),
            publico_alvo=orch_res.get("publico_alvo"),
            objetivo=orch_res.get("objetivo")
        )

        if not copies or not copies.get("opcoes"):
            raise HTTPException(status_code=500, detail="Copywriter falhou em gerar os criativos.")
        
        # 4. Compliance Check
        compliance = ComplianceAgent()
        comp_res = await compliance.validate_copy(copies.get("opcoes", []), orch_res.get("nicho"))
        
        if not comp_res.get("aprovado"):
            detalhes = [p.get("trecho") for p in comp_res.get("problemas", [])]
            raise HTTPException(
                status_code=406, 
                detail=f"Bloqueado pelo Compliance (Risco Meta Ads). Problemas: {detalhes}"
            )

        # 5. Executor (Monta o JSON da Meta API)
        executor = ExecutorAgent()
        best_copy = copies["opcoes"][0] # Na Fase 5 pegamos a primeira APROVADA
        meta_payload = await executor.build_campaign_json(
            produto=orch_res.get("produto"),
            nicho=orch_res.get("nicho"),
            copy=best_copy,
            orcamento_diario=orcamento,
            publico_alvo=orch_res.get("publico_alvo"),
            objetivo=orch_res.get("objetivo")
        )

        if "erro" in meta_payload:
            raise HTTPException(status_code=500, detail=f"Erro no mapeamento Meta: {meta_payload['erro']}")

        # Sucesso no processamento
        return {
            "status": "success",
            "message": "Estrutura finalizada via cascata IA e Guardrails blindados.",
            "data": {
                "campaign_name": meta_payload["campaign"]["name"],
                "daily_budget": orcamento,
                "niche": orch_res.get("nicho"),
                "copies_generated": len(copies["opcoes"]),
                "payload_ready": True
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no Setup de Campanha: {e}")
        raise HTTPException(status_code=500, detail=str(e))
