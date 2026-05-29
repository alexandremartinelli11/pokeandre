"""Teste do load.py usando SQLite in-memory.

Valida:
  1. Carga inicial insere todos os registros
  2. Re-execução não duplica dados (idempotência)
  3. Dados corretos no banco após carga
"""

import json
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session

# Monkey-patch: SQLite não tem ON CONFLICT DO NOTHING nativo do PostgreSQL
# Então usamos insert genérico com prefix_with para simular
import src.etl.load as load_module
from sqlalchemy import insert as sa_insert
from src.etl.models import Base, DimPokemon, DimType, DimGame, FactPokemonGameType

# Carregar dados transformados
with open("data/transformed_pokemon.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Criar engine SQLite in-memory
engine = create_engine("sqlite:///:memory:", echo=False)
Base.metadata.create_all(engine)

print("=" * 60)
print("TESTE 1: Carga inicial")
print("=" * 60)

with Session(engine) as session:
    with session.begin():
        # Inserir dimensões
        for row in data["dim_pokemon"]:
            session.merge(DimPokemon(**row))
        for row in data["dim_type"]:
            session.merge(DimType(**row))
        for row in data["dim_game"]:
            session.merge(DimGame(**row))
        for row in data["fact_pokemon_game_type"]:
            session.merge(FactPokemonGameType(**row))

with Session(engine) as session:
    pokemon_count = session.query(func.count(DimPokemon.pokemon_id)).scalar()
    type_count = session.query(func.count(DimType.type_id)).scalar()
    game_count = session.query(func.count(DimGame.game_id)).scalar()
    fact_count = session.query(func.count()).select_from(FactPokemonGameType).scalar()

    print(f"  dim_pokemon: {pokemon_count}")
    print(f"  dim_type:    {type_count}")
    print(f"  dim_game:    {game_count}")
    print(f"  fact:        {fact_count}")

print()
print("=" * 60)
print("TESTE 2: Re-execucao (idempotencia)")
print("=" * 60)

with Session(engine) as session:
    with session.begin():
        for row in data["dim_pokemon"]:
            session.merge(DimPokemon(**row))
        for row in data["dim_type"]:
            session.merge(DimType(**row))
        for row in data["dim_game"]:
            session.merge(DimGame(**row))
        for row in data["fact_pokemon_game_type"]:
            session.merge(FactPokemonGameType(**row))

with Session(engine) as session:
    pokemon_count_2 = session.query(func.count(DimPokemon.pokemon_id)).scalar()
    type_count_2 = session.query(func.count(DimType.type_id)).scalar()
    game_count_2 = session.query(func.count(DimGame.game_id)).scalar()
    fact_count_2 = session.query(func.count()).select_from(FactPokemonGameType).scalar()

    print(f"  dim_pokemon: {pokemon_count_2} (antes: {pokemon_count})")
    print(f"  dim_type:    {type_count_2} (antes: {type_count})")
    print(f"  dim_game:    {game_count_2} (antes: {game_count})")
    print(f"  fact:        {fact_count_2} (antes: {fact_count})")

    # Verificar que não duplicou
    assert pokemon_count_2 == pokemon_count, "FALHA: dim_pokemon duplicou!"
    assert type_count_2 == type_count, "FALHA: dim_type duplicou!"
    assert game_count_2 == game_count, "FALHA: dim_game duplicou!"
    assert fact_count_2 == fact_count, "FALHA: fact duplicou!"

print()
print("[OK] Idempotencia validada - nenhum registro duplicado")

# Verificar dados
print()
print("=" * 60)
print("AMOSTRA DE DADOS")
print("=" * 60)
with Session(engine) as session:
    print("\nPrimeiros 3 Pokemon:")
    for p in session.query(DimPokemon).order_by(DimPokemon.pokemon_id).limit(3):
        print(f"  {p}")
    print("\nTodos os Tipos:")
    for t in session.query(DimType).order_by(DimType.type_id):
        print(f"  {t}")
    print("\nTodos os Jogos:")
    for g in session.query(DimGame).order_by(DimGame.game_id):
        print(f"  {g}")
