"""Modelos SQLAlchemy para o banco analítico PokeAndre.

Define as tabelas dimensionais e a tabela fato usando Declarative Base.
Utilizado pelo load.py para criar as tabelas e inserir dados.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class DimPokemon(Base):
    """Dimensão Pokémon — um registro por Pokémon único."""
    __tablename__ = "dim_pokemon"

    pokemon_id = Column(Integer, primary_key=True)
    pokemon_name = Column(String(100), nullable=False)

    def __repr__(self):
        return f"<DimPokemon(id={self.pokemon_id}, name='{self.pokemon_name}')>"


class DimType(Base):
    """Dimensão Tipo — tipos únicos de Pokémon (grass, fire, water, etc.)."""
    __tablename__ = "dim_type"

    type_id = Column(Integer, primary_key=True)
    type_name = Column(String(50), nullable=False)

    def __repr__(self):
        return f"<DimType(id={self.type_id}, name='{self.type_name}')>"


class DimGame(Base):
    """Dimensão Jogo — jogos únicos onde os Pokémon aparecem."""
    __tablename__ = "dim_game"

    game_id = Column(Integer, primary_key=True)
    game_name = Column(String(100), nullable=False)

    def __repr__(self):
        return f"<DimGame(id={self.game_id}, name='{self.game_name}')>"


class FactPokemonGameType(Base):
    """Tabela Fato — relaciona Pokémon, Tipo e Jogo.
    
    Chave primária composta: (pokemon_id, type_id, game_id).
    """
    __tablename__ = "fact_pokemon_game_type"

    pokemon_id = Column(Integer, ForeignKey("dim_pokemon.pokemon_id"), nullable=False)
    type_id = Column(Integer, ForeignKey("dim_type.type_id"), nullable=False)
    game_id = Column(Integer, ForeignKey("dim_game.game_id"), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("pokemon_id", "type_id", "game_id"),
    )

    def __repr__(self):
        return f"<Fact(pokemon={self.pokemon_id}, type={self.type_id}, game={self.game_id})>"
