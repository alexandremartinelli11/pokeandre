-- Script de inicialização do PostgreSQL
-- Executado automaticamente na primeira inicialização do container
-- Cria os bancos e usuários necessários para o projeto

-- Banco de dados do projeto (data warehouse)
CREATE USER pokeandre WITH PASSWORD 'pokeandre';
CREATE DATABASE pokeandre OWNER pokeandre;

-- Banco de dados de metadados do Airflow
CREATE USER airflow WITH PASSWORD 'airflow';
CREATE DATABASE airflow OWNER airflow;
