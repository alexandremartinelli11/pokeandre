import json
import logging
import os

# Configurando log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(filename)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Diretório para arquivos intermediários
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')


def _load_raw_data(filepath=None):
    """Carrega os dados brutos do JSON gerado pelo extract."""
    if filepath is None:
        filepath = os.path.join(DATA_DIR, "raw_pokemon.json")

    logger.info(f"Carregando dados brutos de: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    logger.info(f"Total de registros brutos carregados: {len(data)}")
    return data


def _rule_1_convert_id(records):
    """Regra 1: Converter id de string para inteiro."""
    converted = 0
    for record in records:
        record['id'] = int(record['id'])
        converted += 1
    logger.info(f"Regra 1 — IDs convertidos para inteiro: {converted}")
    return records


def _rule_2_standardize_names(records):
    """Regra 2: Padronizar nomes com strip() e lower()."""
    for record in records:
        record['name'] = record['name'].strip().lower()
    logger.info(f"Regra 2 — Nomes padronizados (strip + lower): {len(records)}")
    return records


def _rule_3_remove_duplicates(records):
    """Regra 3: Remover registros duplicados pelo critério id."""
    seen_ids = set()
    unique = []
    duplicates = 0
    for record in records:
        if record['id'] not in seen_ids:
            seen_ids.add(record['id'])
            unique.append(record)
        else:
            duplicates += 1
    logger.info(f"Regra 3 — Duplicatas removidas: {duplicates} | Registros únicos: {len(unique)}")
    return unique


def _rule_4_5_filter_games_and_explode(records):
    """Regra 4 e 5: Filtrar os 2 primeiros jogos e explodir tipos e jogos.
    
    Retorna uma lista de tuplas (pokemon_id, type_name, game_name)
    representando o produto cartesiano de tipos × jogos (máx. 2) por Pokémon.
    """
    exploded = []
    for record in records:
        types = record.get('types', [])
        # Regra 5: manter apenas os 2 primeiros jogos (dupla de estreia)
        games = record.get('games', [])[:2]

        pokemon_id = record['id']

        for type_name in types:
            for game_name in games:
                exploded.append({
                    'pokemon_id': pokemon_id,
                    'pokemon_name': record['name'],
                    'type_name': type_name.strip().lower(),
                    'game_name': game_name.strip().lower()
                })

    logger.info(f"Regra 4+5 — Registros explodidos (tipos × 2 jogos): {len(exploded)}")
    return exploded


def _rule_6_build_relational(exploded):
    """Regra 6: Gerar estruturas relacionais (dimensões + fato).
    
    IDs de dim_type e dim_game são gerados internamente:
    valores únicos ordenados alfabeticamente, indexados de 1 a N.
    """
    # --- dim_pokemon ---
    pokemon_map = {}
    for row in exploded:
        pid = row['pokemon_id']
        if pid not in pokemon_map:
            pokemon_map[pid] = row['pokemon_name']

    dim_pokemon = [
        {"pokemon_id": pid, "pokemon_name": name}
        for pid, name in sorted(pokemon_map.items())
    ]

    # --- dim_type ---
    unique_types = sorted({row['type_name'] for row in exploded})
    type_name_to_id = {name: idx + 1 for idx, name in enumerate(unique_types)}
    dim_type = [
        {"type_id": type_name_to_id[name], "type_name": name}
        for name in unique_types
    ]

    # --- dim_game ---
    unique_games = sorted({row['game_name'] for row in exploded})
    game_name_to_id = {name: idx + 1 for idx, name in enumerate(unique_games)}
    dim_game = [
        {"game_id": game_name_to_id[name], "game_name": name}
        for name in unique_games
    ]

    # --- fact_pokemon_game_type ---
    fact_set = set()
    fact = []
    for row in exploded:
        key = (row['pokemon_id'], type_name_to_id[row['type_name']], game_name_to_id[row['game_name']])
        if key not in fact_set:
            fact_set.add(key)
            fact.append({
                "pokemon_id": key[0],
                "type_id": key[1],
                "game_id": key[2]
            })

    logger.info(f"Regra 6 — dim_pokemon: {len(dim_pokemon)} | dim_type: {len(dim_type)} | dim_game: {len(dim_game)} | fact: {len(fact)}")
    return {
        "dim_pokemon": dim_pokemon,
        "dim_type": dim_type,
        "dim_game": dim_game,
        "fact_pokemon_game_type": fact
    }


def transform_pokemon_data(raw_data=None):
    """Pipeline de transformação completo.
    
    Aplica as 6 regras de negócio e retorna as 4 estruturas relacionais.
    Salva o resultado em data/transformed_pokemon.json.
    """
    # Carregar dados brutos
    if raw_data is None:
        raw_data = _load_raw_data()

    logger.info("=" * 60)
    logger.info("INICIANDO TRANSFORMAÇÃO")
    logger.info("=" * 60)

    # Regra 1: Converter id para inteiro
    records = _rule_1_convert_id(raw_data)

    # Regra 2: Padronizar nomes
    records = _rule_2_standardize_names(records)

    # Regra 3: Remover duplicatas por id
    records = _rule_3_remove_duplicates(records)

    # Regras 4 e 5: Filtrar 2 primeiros jogos + explodir tipos × jogos
    exploded = _rule_4_5_filter_games_and_explode(records)

    # Regra 6: Gerar estruturas relacionais
    result = _rule_6_build_relational(exploded)

    # Salvar resultado em arquivo intermediário
    os.makedirs(DATA_DIR, exist_ok=True)
    output_path = os.path.join(DATA_DIR, "transformed_pokemon.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    logger.info(f"Dados transformados salvos em: {output_path}")

    logger.info("=" * 60)
    logger.info("TRANSFORMAÇÃO CONCLUÍDA")
    logger.info("=" * 60)

    return result


if __name__ == "__main__":
    result = transform_pokemon_data()

    print("\n--- dim_pokemon (primeiros 5) ---")
    for row in result["dim_pokemon"][:5]:
        print(row)

    print("\n--- dim_type ---")
    for row in result["dim_type"]:
        print(row)

    print("\n--- dim_game ---")
    for row in result["dim_game"]:
        print(row)

    print(f"\n--- fact_pokemon_game_type ({len(result['fact_pokemon_game_type'])} registros, primeiros 10) ---")
    for row in result["fact_pokemon_game_type"][:10]:
        print(row)
