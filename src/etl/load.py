"""Módulo de carga (Load) — persiste dados transformados no PostgreSQL.

Regras:
  1. Idempotência: INSERT ... ON CONFLICT DO NOTHING
  2. Transações: cada tabela em bloco transacional
  3. Logs: registra antes e depois de cada carga
  4. Falha explícita: raise com contexto em caso de erro
  5. Ordem de carga: dimensões primeiro, fato por último
"""

import json
import logging
import os

from sqlalchemy import create_engine, insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from src.etl.config import config
from src.etl.models import Base, DimPokemon, DimType, DimGame, FactPokemonGameType

# Configurando log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(filename)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Diretório para arquivos intermediários
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')


def _build_connection_url():
    """Constrói a URL de conexão do PostgreSQL a partir das variáveis de ambiente."""
    url = (
        f"postgresql://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}"
        f"@{config.POSTGRES_HOST}:{config.POSTGRES_PORT}/{config.POSTGRES_DB}"
    )
    return url


def _get_engine(connection_url=None):
    """Cria e retorna o engine SQLAlchemy."""
    if connection_url is None:
        connection_url = _build_connection_url()
    engine = create_engine(connection_url, echo=False)
    return engine


def _load_table(session, model, records, table_name):
    """Carrega registros em uma tabela com idempotência.
    
    Usa INSERT ... ON CONFLICT DO NOTHING para evitar duplicatas.
    """
    if not records:
        logger.warning(f"{table_name}: nenhum registro para carregar")
        return 0

    logger.info(f"{table_name}: carregando {len(records)} registros...")

    try:
        stmt = pg_insert(model).values(records).on_conflict_do_nothing()
        result = session.execute(stmt)
        inserted = result.rowcount
        logger.info(f"{table_name}: {inserted} novos registros inseridos ({len(records) - inserted} já existiam)")
        return inserted
    except Exception as e:
        raise RuntimeError(f"Erro ao carregar {table_name}: {e}") from e


def load_pokemon_data(data=None, connection_url=None):
    """Carrega os dados transformados no PostgreSQL.
    
    Lê de data/transformed_pokemon.json se nenhum dado for passado.
    Cria as tabelas se não existirem.
    Ordem: dim_pokemon → dim_type → dim_game → fact_pokemon_game_type.
    """
    # Carregar dados transformados
    if data is None:
        filepath = os.path.join(DATA_DIR, "transformed_pokemon.json")
        logger.info(f"Carregando dados transformados de: {filepath}")
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

    engine = _get_engine(connection_url)

    # Criar tabelas se não existirem
    logger.info("Criando tabelas (se nao existirem)...")
    Base.metadata.create_all(engine)

    logger.info("=" * 60)
    logger.info("INICIANDO CARGA NO BANCO")
    logger.info("=" * 60)

    total_inserted = 0

    with Session(engine) as session:
        try:
            # Ordem de carga: dimensões primeiro, fato por último
            with session.begin():
                total_inserted += _load_table(
                    session, DimPokemon, data["dim_pokemon"], "dim_pokemon"
                )
                total_inserted += _load_table(
                    session, DimType, data["dim_type"], "dim_type"
                )
                total_inserted += _load_table(
                    session, DimGame, data["dim_game"], "dim_game"
                )
                total_inserted += _load_table(
                    session, FactPokemonGameType, data["fact_pokemon_game_type"], "fact_pokemon_game_type"
                )

        except Exception as e:
            logger.error(f"Erro durante a carga — transacao revertida: {e}")
            raise

    logger.info("=" * 60)
    logger.info(f"CARGA CONCLUIDA — {total_inserted} registros inseridos no total")
    logger.info("=" * 60)

    return total_inserted


if __name__ == "__main__":
    inserted = load_pokemon_data()
    print(f"\n[OK] Carga concluida: {inserted} registros inseridos")
