"""
Constantes e limites da Google Ads API.
"""

# Versão estável (2026)
GOOGLE_ADS_API_VERSION = "v18"

# Mapeamento de Intenção -> Estratégia de Lance
OBJECTIVE_STRATEGY = {
    "OUTCOME_TRAFFIC": "MAXIMIZE_CLICKS",
    "OUTCOME_LEADS": "MAXIMIZE_CONVERSIONS",
    "OUTCOME_SALES": "MAXIMIZE_CONVERSION_VALUE",
    "OUTCOME_AWARENESS": "MAXIMIZE_IMPRESSIONS",
}

# Limites do Google RSA (Responsive Search Ads)
# Essencial para o Agente Copywriter e Executor
RSA_CONFIG = {
    "headlines": {
        "min": 3,
        "max": 15,
        "max_chars": 30
    },
    "descriptions": {
        "min": 2,
        "max": 4,
        "max_chars": 90
    }
}

# Tipos de correspondência de Keyword
KEYWORD_MATCH_TYPES = [
    "EXACT",
    "PHRASE",
    "BROAD"
]

# Unidade monetária do Google Ads (Micros)
# 1 BRL = 1.000.000 Micros
MICROS_MULTIPLIER = 1_000_000

# Métricas GAQL (Google Ads Query Language)
GAQL_CAMPAIGN_METRICS = """
    SELECT
        campaign.id,
        campaign.name,
        campaign.status,
        metrics.cost_micros,
        metrics.impressions,
        metrics.clicks,
        metrics.ctr,
        metrics.average_cpc,
        metrics.conversions,
        metrics.cost_per_conversion,
        metrics.conversions_value
    FROM campaign
    WHERE segments.date DURING {date_range}
"""
