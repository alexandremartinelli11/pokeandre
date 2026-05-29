import json
import logging
import os

# Configurando log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(filename)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Diretório para arquivos intermediários
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')


def _check_null_ids(data):
    """Verifica se existem IDs nulos em qualquer tabela."""
    errors = []

    for row in data["dim_pokemon"]:
        if row.get("pokemon_id") is None:
            errors.append(f"dim_pokemon: pokemon_id nulo encontrado em {row}")

    for row in data["dim_type"]:
        if row.get("type_id") is None:
            errors.append(f"dim_type: type_id nulo encontrado em {row}")

    for row in data["dim_game"]:
        if row.get("game_id") is None:
            errors.append(f"dim_game: game_id nulo encontrado em {row}")

    for row in data["fact_pokemon_game_type"]:
        if row.get("pokemon_id") is None:
            errors.append(f"fact: pokemon_id nulo em {row}")
        if row.get("type_id") is None:
            errors.append(f"fact: type_id nulo em {row}")
        if row.get("game_id") is None:
            errors.append(f"fact: game_id nulo em {row}")

    if errors:
        raise ValueError(f"IDs nulos encontrados ({len(errors)} ocorrências):\n" + "\n".join(errors))

    logger.info("✔ Validação IDs nulos: APROVADO")


def _check_empty_names(data):
    """Verifica se existem nomes vazios ou somente espaços."""
    errors = []

    for row in data["dim_pokemon"]:
        name = row.get("pokemon_name", "")
        if not name or not name.strip():
            errors.append(f"dim_pokemon: pokemon_name vazio para id={row.get('pokemon_id')}")

    for row in data["dim_type"]:
        name = row.get("type_name", "")
        if not name or not name.strip():
            errors.append(f"dim_type: type_name vazio para id={row.get('type_id')}")

    for row in data["dim_game"]:
        name = row.get("game_name", "")
        if not name or not name.strip():
            errors.append(f"dim_game: game_name vazio para id={row.get('game_id')}")

    if errors:
        raise ValueError(f"Nomes vazios encontrados ({len(errors)} ocorrências):\n" + "\n".join(errors))

    logger.info("✔ Validação nomes vazios: APROVADO")


def _check_duplicate_ids(data):
    """Verifica se existem IDs duplicados nas tabelas de dimensão."""
    errors = []

    # dim_pokemon
    pokemon_ids = [row["pokemon_id"] for row in data["dim_pokemon"]]
    dupes = [pid for pid in set(pokemon_ids) if pokemon_ids.count(pid) > 1]
    if dupes:
        errors.append(f"dim_pokemon: IDs duplicados: {dupes}")

    # dim_type
    type_ids = [row["type_id"] for row in data["dim_type"]]
    dupes = [tid for tid in set(type_ids) if type_ids.count(tid) > 1]
    if dupes:
        errors.append(f"dim_type: IDs duplicados: {dupes}")

    # dim_game
    game_ids = [row["game_id"] for row in data["dim_game"]]
    dupes = [gid for gid in set(game_ids) if game_ids.count(gid) > 1]
    if dupes:
        errors.append(f"dim_game: IDs duplicados: {dupes}")

    if errors:
        raise ValueError(f"Duplicatas encontradas:\n" + "\n".join(errors))

    logger.info("✔ Validação duplicatas: APROVADO")


def _check_data_types(data):
    """Verifica se os tipos de dados estão corretos."""
    errors = []

    for row in data["dim_pokemon"]:
        if not isinstance(row.get("pokemon_id"), int):
            errors.append(f"dim_pokemon: pokemon_id não é int: {row}")
        if not isinstance(row.get("pokemon_name"), str):
            errors.append(f"dim_pokemon: pokemon_name não é str: {row}")

    for row in data["dim_type"]:
        if not isinstance(row.get("type_id"), int):
            errors.append(f"dim_type: type_id não é int: {row}")
        if not isinstance(row.get("type_name"), str):
            errors.append(f"dim_type: type_name não é str: {row}")

    for row in data["dim_game"]:
        if not isinstance(row.get("game_id"), int):
            errors.append(f"dim_game: game_id não é int: {row}")
        if not isinstance(row.get("game_name"), str):
            errors.append(f"dim_game: game_name não é str: {row}")

    for row in data["fact_pokemon_game_type"]:
        for key in ("pokemon_id", "type_id", "game_id"):
            if not isinstance(row.get(key), int):
                errors.append(f"fact: {key} não é int: {row}")

    if errors:
        raise ValueError(f"Tipos de dados inválidos ({len(errors)} ocorrências):\n" + "\n".join(errors))

    logger.info("✔ Validação tipos de dados: APROVADO")


def _check_orphan_fks(data):
    """Verifica se toda FK na fato existe nas dimensões correspondentes."""
    pokemon_ids = {row["pokemon_id"] for row in data["dim_pokemon"]}
    type_ids = {row["type_id"] for row in data["dim_type"]}
    game_ids = {row["game_id"] for row in data["dim_game"]}

    errors = []
    for row in data["fact_pokemon_game_type"]:
        if row["pokemon_id"] not in pokemon_ids:
            errors.append(f"fact: pokemon_id={row['pokemon_id']} não existe em dim_pokemon")
        if row["type_id"] not in type_ids:
            errors.append(f"fact: type_id={row['type_id']} não existe em dim_type")
        if row["game_id"] not in game_ids:
            errors.append(f"fact: game_id={row['game_id']} não existe em dim_game")

    if errors:
        raise ValueError(f"FKs órfãs encontradas ({len(errors)} ocorrências):\n" + "\n".join(errors))

    logger.info("✔ Validação FKs órfãs: APROVADO")


def _check_minimum_volume(data):
    """Verifica se há pelo menos 1 registro em cada tabela."""
    errors = []

    for table_name in ("dim_pokemon", "dim_type", "dim_game", "fact_pokemon_game_type"):
        if len(data.get(table_name, [])) == 0:
            errors.append(f"{table_name}: tabela vazia (0 registros)")

    if errors:
        raise ValueError(f"Volume mínimo não atingido:\n" + "\n".join(errors))

    logger.info("✔ Validação volume mínimo: APROVADO")


def validate_quality(data=None):
    """Executa todas as validações de qualidade nos dados transformados.

    Lê de data/transformed_pokemon.json se nenhum dado for passado.
    Retorna True se todas as validações passarem.
    Levanta ValueError se alguma validação falhar.
    """
    # Carregar dados transformados
    if data is None:
        filepath = os.path.join(DATA_DIR, "transformed_pokemon.json")
        logger.info(f"Carregando dados transformados de: {filepath}")
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

    logger.info("=" * 60)
    logger.info("INICIANDO VALIDAÇÃO DE QUALIDADE")
    logger.info("=" * 60)
    logger.info(
        f"Volumes: dim_pokemon={len(data['dim_pokemon'])} | "
        f"dim_type={len(data['dim_type'])} | "
        f"dim_game={len(data['dim_game'])} | "
        f"fact={len(data['fact_pokemon_game_type'])}"
    )

    # Executa todas as validações
    _check_null_ids(data)
    _check_empty_names(data)
    _check_duplicate_ids(data)
    _check_data_types(data)
    _check_orphan_fks(data)
    _check_minimum_volume(data)

    logger.info("=" * 60)
    logger.info("TODAS AS VALIDAÇÕES APROVADAS")
    logger.info("=" * 60)

    return True


if __name__ == "__main__":
    try:
        result = validate_quality()
        print(f"\n[OK] Qualidade aprovada: {result}")
    except ValueError as e:
        print(f"\n[FALHA] Erro de qualidade:\n{e}")
