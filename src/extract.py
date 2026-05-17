import csv
import logging
import requests
import wget
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Importando variáveis de ambiente carregadas no config
from config import config

# Configurando log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(filename)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_pokemon_data(csv_url=None):
    if csv_url is None:
        csv_url = config.CSV_BASE_LINK
        
    csv_path = "./Pokemon.csv"
    
    logger.info(f"Fazendo download do arquivo CSV via wget de: {csv_url}")
    # Remove se já existir para garantir que o wget baixe o mais recente com o nome correto
    if os.path.exists(csv_path):
        os.remove(csv_path)
    
    wget.download(csv_url, out=csv_path)
    print() # Quebra de linha após o output do wget
    
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
            
    return extracted_data

if __name__ == "__main__":
    data = extract_pokemon_data()
    
    print("\n--- Últimos 5 registros extraídos ---")
    for item in data[-5:]:
        print(item)
