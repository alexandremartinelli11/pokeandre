import os
from dotenv import load_dotenv, find_dotenv

class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._init_config()
        return cls._instance

    def _init_config(self):
        # Carrega as variáveis do arquivo .env
        load_dotenv(find_dotenv())
        
        self.API_BASE_LINK = os.getenv("API_BASE_LINK", "https://pokeapi.co/api/v2/pokemon")
        self.CSV_BASE_LINK = os.getenv("CSV_BASE_LINK", "https://gist.githubusercontent.com/armgilles/194bcff35001e7eb53a2a8b441e8b2c6/raw/92200bc0a673d5ce2110aaad4544ed6c4010f687/pokemon.csv")
        
        # Limite de Pokémon para desenvolvimento (None = sem limite)
        _limit = os.getenv("POKEMON_LIMIT")
        self.POKEMON_LIMIT = int(_limit) if _limit else None

        # Configurações do PostgreSQL
        self.POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
        self.POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
        self.POSTGRES_DB = os.getenv("POSTGRES_DB", "pokeandre")
        self.POSTGRES_USER = os.getenv("POSTGRES_USER", "pokeandre")
        self.POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "pokeandre")

# Instância Singleton exportada
config = Config()
