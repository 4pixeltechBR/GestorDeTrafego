"""
Database — Motor SQLite assíncrono com WAL mode.

Gerencia conexões e criação de tabelas para:
- Campanhas criadas
- Histórico de métricas
- Audit log de decisões dos agentes
"""

import logging
import aiosqlite
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
    await db.execute("PRAGMA journal_mode=WAL")
    return db
