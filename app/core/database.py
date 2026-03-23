"""
Database — Motor SQLite assíncrono com WAL mode.

Gerencia conexões e criação de tabelas para:
- Campanhas criadas
- Histórico de métricas
- Audit log de decisões dos agentes
"""

import logging
import aiosqlite
import json
import uuid
from pathlib import Path

from config.settings import BASE_DIR

logger = logging.getLogger(__name__)

# Caminho do banco de dados (na pasta data/ que está no .gitignore)
DB_DIR = BASE_DIR / "data"
DB_PATH = DB_DIR / "gestor_trafego.db"


async def init_db() -> None:
    """Inicializa o banco de dados e cria tabelas se não existirem."""
    DB_DIR.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(str(DB_PATH)) as db:
        # WAL mode para melhor performance de leitura
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")

        # --- Tabela de Campanhas ---
        await db.execute("""
            CREATE TABLE IF NOT EXISTS campaigns (
                id TEXT PRIMARY KEY,
                meta_campaign_id TEXT,
                name TEXT NOT NULL,
                niche TEXT,
                product TEXT,
                daily_budget REAL,
                status TEXT DEFAULT 'DRAFT',
                platform TEXT DEFAULT 'meta',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                copy_title TEXT,
                copy_body TEXT,
                targeting_json TEXT,
                meta_response_json TEXT
            )
        """)

        # --- Tabela de Métricas (Snapshots diários) ---
        await db.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id TEXT NOT NULL,
                date TEXT NOT NULL,
                spend REAL DEFAULT 0,
                impressions INTEGER DEFAULT 0,
                clicks INTEGER DEFAULT 0,
                cpc REAL DEFAULT 0,
                ctr REAL DEFAULT 0,
                cpm REAL DEFAULT 0,
                roas REAL DEFAULT 0,
                conversions INTEGER DEFAULT 0,
                collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
            )
        """)

        # --- Tabela de Audit Log ---
        await db.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                agent TEXT NOT NULL,
                action TEXT NOT NULL,
                campaign_id TEXT,
                input_summary TEXT,
                output_summary TEXT,
                llm_provider TEXT,
                llm_model TEXT,
                tokens_used INTEGER DEFAULT 0,
                success INTEGER DEFAULT 1
            )
        """)

        # --- Tabela de Configurações de Nicho por Campanha ---
        await db.execute("""
            CREATE TABLE IF NOT EXISTS campaign_niche_config (
                campaign_id TEXT PRIMARY KEY,
                niche_template TEXT,
                custom_benchmarks_json TEXT,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
            )
        """)

        await db.commit()
        logger.info(f"✅ Banco de dados inicializado: {DB_PATH}")


async def get_db() -> aiosqlite.Connection:
    """Retorna uma conexão ao banco de dados."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    return db


async def save_pending_campaign(pipeline_result: dict) -> str:
    """
    Salva resultado do pipeline como campanha PENDENTE (aguardando aprovação).

    Returns:
        pending_id: ID interno gerado para esta campanha pendente.
    """
    pending_id = str(uuid.uuid4())[:12]

    db = await get_db()
    await db.execute(
        """
        INSERT INTO campaigns
            (id, name, niche, product, daily_budget, status,
             platform, copy_title, copy_body, targeting_json, meta_response_json)
        VALUES (?, ?, ?, ?, ?, 'PENDING', ?, ?, ?, ?, ?)
        """,
        (
            pending_id,
            pipeline_result.get("produto", "Campanha IA")[:100],
            pipeline_result.get("nicho", "servicos"),
            pipeline_result.get("produto", ""),
            pipeline_result.get("orcamento", 0),
            pipeline_result.get("canal", "meta"),
            pipeline_result["copies"][0].get("titulo", "") if pipeline_result.get("copies") else "",
            pipeline_result["copies"][0].get("texto_principal", "") if pipeline_result.get("copies") else "",
            json.dumps(
                pipeline_result.get("orchestration", {}).get("publico_alvo", {}),
                ensure_ascii=False
            ),
            json.dumps(pipeline_result, ensure_ascii=False),
        ),
    )
    await db.commit()
    await db.close()

    logger.info(f"[DB] Campanha pendente salva: {pending_id}")
    return pending_id


async def get_pending_campaign(pending_id: str) -> dict | None:
    """Busca uma campanha pendente pelo ID interno."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM campaigns WHERE id = ? AND status = 'PENDING'",
        (pending_id,),
    )
    row = await cursor.fetchone()
    await db.close()

    if not row:
        return None

    result = dict(row)
    if result.get("meta_response_json"):
        try:
            result["pipeline_result"] = json.loads(result["meta_response_json"])
        except Exception:
            pass
    return result


async def update_campaign_status(campaign_id: str, status: str, meta_id: str = None) -> None:
    """Atualiza o status de uma campanha no banco local."""
    db = await get_db()
    if meta_id:
        await db.execute(
            "UPDATE campaigns SET status = ?, meta_campaign_id = ? WHERE id = ?",
            (status, meta_id, campaign_id),
        )
    else:
        await db.execute(
            "UPDATE campaigns SET status = ? WHERE id = ?",
            (status, campaign_id),
        )
    await db.commit()
    await db.close()
