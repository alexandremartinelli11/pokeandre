import csv
import json
import logging
import os
import requests
import wget
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Importando variáveis de ambiente carregadas no config
from src.etl.config import config

# Configurando log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(filename)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Diretório para arquivos intermediários
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')


def extract_pokemon_data(csv_url=None):
    """Extrai dados de Pokémon do CSV e enriquece via PokéAPI.
    
    Salva o resultado bruto em data/raw_pokemon.json.
    Respeita POKEMON_LIMIT do .env para limitar durante desenvolvimento.
    """
    if csv_url is None:
        csv_url = config.CSV_BASE_LINK
        
    csv_path = os.path.join(DATA_DIR, "Pokemon.csv")
    
    # Garante que o diretório data/ existe
    os.makedirs(DATA_DIR, exist_ok=True)
    
    logger.info(f"Fazendo download do arquivo CSV via wget de: {csv_url}")
    # Remove se já existir para garantir que o wget baixe o mais recente com o nome correto
    if os.path.exists(csv_path):
        os.remove(csv_path)
    
    wget.download(csv_url, out=csv_path)
    print()  # Quebra de linha após o output do wget
    
    all_pokemon = []
    
    # Ler o arquivo csv, guardar id e nome. Intencionalmente guardando duplicados para limpar no transform.
    total_csv_lines = 0
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Pula o header
        for row in reader:
            total_csv_lines += 1
            if not row:
                continue
            dex_id = row[0]
            name = row[1]
            all_pokemon.append((dex_id, name))
                
    logger.info(f"Total de linhas lidas do CSV: {total_csv_lines}")
    logger.info(f"Total de Pokémon armazenados: {len(all_pokemon)}")
    
    # Aplica limite de desenvolvimento se configurado
    if config.POKEMON_LIMIT:
        all_pokemon = all_pokemon[:config.POKEMON_LIMIT]
        logger.info(f"POKEMON_LIMIT ativo: processando apenas {config.POKEMON_LIMIT} Pokémon")
                
    # Configurar requests com retry para evitar falhas de rede na API
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    
    extracted_data = []
    api_calls_made = 0
    
    # Para cada um dos entries, add o num da dex no fim do link da api
    for dex_id, name in all_pokemon:
        url = f"{config.API_BASE_LINK}/{dex_id}"
        api_calls_made += 1
        
        try:
            response = session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Pegar a lista INTEIRA de jogos intencionalmente
                # A filtragem dos 2 primeiros será feita no transform.py
                games = [g['version']['name'] for g in data.get('game_indices', [])]
                
                # Guardar APENAS os nomes dos tipos
                types = [t['type']['name'] for t in data.get('types', [])]
                
                extracted_data.append({
                    "id": dex_id,
                    "name": name,
                    "games": games,
                    "types": types
                })
            else:
                logger.warning(f"Falha ao buscar ID {dex_id}. Status HTTP: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de rede ao buscar ID {dex_id}: {e}")
        except ValueError as e:
            logger.error(f"Erro ao converter JSON do ID {dex_id}: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado ao processar ID {dex_id}: {e}")
            
    logger.info(f"Total de chamadas feitas a API: {api_calls_made}")
    logger.info(f"Total de respostas validas da API: {len(extracted_data)}")
    
    # Salvar dados brutos em arquivo intermediário
    output_path = os.path.join(DATA_DIR, "raw_pokemon.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(extracted_data, f, ensure_ascii=False, indent=2)
    logger.info(f"Dados brutos salvos em: {output_path}")
            
    return extracted_data


if __name__ == "__main__":
    data = extract_pokemon_data()
    
    print(f"\n--- Últimos 5 registros extraídos ({len(data)} total) ---")
    for item in data[-5:]:
        print(item)
