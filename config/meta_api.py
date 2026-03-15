"""
Constantes e configurações da Meta Marketing API.
"""

# Versão atual da API (atualizada em Março 2026)
META_API_VERSION = "v25.0"
META_GRAPH_URL = f"https://graph.facebook.com/{META_API_VERSION}"

# Endpoints principais
ENDPOINTS = {
    "campaigns": "/{ad_account_id}/campaigns",
    "adsets": "/{ad_account_id}/adsets",
    "ads": "/{ad_account_id}/ads",
    "adcreatives": "/{ad_account_id}/adcreatives",
    "insights": "/{object_id}/insights",
    "images": "/{ad_account_id}/adimages",
}

# Objetivos de campanha válidos (Meta API v25.0)
CAMPAIGN_OBJECTIVES = [
    "OUTCOME_AWARENESS",
    "OUTCOME_ENGAGEMENT",
    "OUTCOME_LEADS",
    "OUTCOME_SALES",
    "OUTCOME_TRAFFIC",
    "OUTCOME_APP_PROMOTION",
]

# Status de campanha
CAMPAIGN_STATUS = {
    "ACTIVE": "ACTIVE",
    "PAUSED": "PAUSED",
    "DELETED": "DELETED",
    "ARCHIVED": "ARCHIVED",
}

# Categorias especiais de anúncio (obrigatórias quando aplicável)
SPECIAL_AD_CATEGORIES = [
    "CREDIT",
    "EMPLOYMENT",
    "HOUSING",
    "SOCIAL_ISSUES_ELECTIONS_POLITICS",
]

# Métricas de Insights mais utilizadas
INSIGHT_FIELDS = [
    "campaign_name",
    "spend",
    "impressions",
    "clicks",
    "cpc",
    "cpm",
    "ctr",
    "reach",
    "frequency",
    "actions",
    "cost_per_action_type",
    "purchase_roas",
]

# Delays mínimos entre requisições Meta (anti-ban)
META_REQUEST_DELAY_MIN = 1.0  # segundos
META_REQUEST_DELAY_MAX = 3.0  # segundos (jitter aleatório)
