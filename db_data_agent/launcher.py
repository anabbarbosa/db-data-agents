import os
import hashlib
from db_data_agent.etl.controller import ETLController
from db_data_agent.agent.controller import AgentController
from sqlalchemy import create_engine, text
import click

def _hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def _authenticate_user(username: str, password: str):
    """Authenticate user and return user data"""
    # Configuração do banco (mesmo do controller)
    PGUSER = os.getenv("PGUSER", "postgres")
    PGPASSWORD = os.getenv("PGPASSWORD", "mypassword")
    PGHOST = os.getenv("PGHOST", "localhost")
    PGPORT = os.getenv("PGPORT", "5432")
    PGDATABASE = os.getenv("PGDATABASE", "postgres")

    DATABASE_URL = f"postgresql+psycopg://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}"
    engine = create_engine(DATABASE_URL, echo=False, future=True)
    
    try:
        with engine.connect() as conn:
            password_hash = _hash_password(password)
            row = conn.execute(text(
                "SELECT id, username, user_group FROM agent.users WHERE username = :username AND password_hash = :pwd"
            ), {"username": username, "pwd": password_hash}).fetchone()
            if row:
                return {"id": row[0], "username": row[1], "user_group": row[2]}
    except Exception as e:
        print(f"Erro na autenticação: {e}")
    return None

@click.command()
@click.option('--etl', type=click.BOOL, required=True)
@click.option('--agent', type=click.BOOL, required=True)
@click.option('--amazon', type=click.BOOL, default=None)
@click.option('--spotify', type=click.BOOL, default=None)
@click.option('--user-group', type=click.STRING, default=None)
@click.option('--username', type=click.STRING, default=None)
@click.option('--password', type=click.STRING, default=None)

def run(etl, agent, amazon, spotify, user_group, username, password):
    # Sistema de autenticação
    authenticated_user = None
    final_user_group = user_group
    
    if username and password:
        # Login com usuário e senha
        authenticated_user = _authenticate_user(username, password)
        if authenticated_user:
            final_user_group = authenticated_user['user_group']
            print(f"✅ Login realizado com sucesso!")
            print(f"Usuário: {authenticated_user['username']}")
            print(f"User Group: {final_user_group}")
        else:
            print("❌ Erro: Username ou senha incorretos")
            return
    elif username or password:
        print("❌ Erro: É necessário fornecer tanto --username quanto --password")
        return
    elif user_group:
        print(f"⚠️  Usando user_group especificado: {user_group}")
        final_user_group = user_group
    else:
        print("⚠️  Usando user_group padrão: amazon")
        final_user_group = 'amazon'
    
    # Determina os parâmetros amazon e spotify baseado no user_group final
    if final_user_group.lower() == 'spotify':
        amazon = False if amazon is None else amazon
        spotify = True if spotify is None else spotify
    else:  # default para amazon
        amazon = True if amazon is None else amazon
        spotify = False if spotify is None else spotify
    
    print(f"ETL parameters - Amazon: {amazon}, Spotify: {spotify}")
        
    if etl: 
        controller = ETLController()
        controller.etl(amazon=amazon, spotify=spotify)
        
    if agent:
        controller = AgentController()
        question = input("Digite a sua pergunta: ")
        controller.run(question, user_group=final_user_group)