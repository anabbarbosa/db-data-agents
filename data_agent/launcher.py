import os
import hashlib
from data_agent.etl.controller import ETLController
from data_agent.agent.controller import AgentController
from sqlalchemy import create_engine, text
import click

def _hash_password(password: str) -> str:
    """hash the password using sha-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def _authenticate_user(username: str, password: str):
    """authenticate the user and return user data"""
    # database configuration for the current controller
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
        print(f"authentication error: {e}")
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
    # authentication flow
    authenticated_user = None
    final_user_group = user_group
    
    if username and password:
        # login with username and password
        authenticated_user = _authenticate_user(username, password)
        if authenticated_user:
            final_user_group = authenticated_user['user_group']
            print(f"✅ login successful!")
            print(f"user: {authenticated_user['username']}")
            print(f"user group: {final_user_group}")
        else:
            print("❌ error: username or password is invalid")
            return
    elif username or password:
        print("❌ error: both --username and --password are required")
        return
    elif user_group:
        print(f"⚠️ using the specified user_group: {user_group}")
        final_user_group = user_group
    else:
        print("⚠️ using the default user_group: amazon")
        final_user_group = 'amazon'
    
    # determine amazon and spotify parameters based on the final user_group
    if final_user_group.lower() == 'spotify':
        amazon = False if amazon is None else amazon
        spotify = True if spotify is None else spotify
    else:  # default to amazon
        amazon = True if amazon is None else amazon
        spotify = False if spotify is None else spotify
    
    print(f"ETL parameters - Amazon: {amazon}, Spotify: {spotify}")
        
    if etl: 
        controller = ETLController()
        controller.etl(amazon=amazon, spotify=spotify)
        
    if agent:
        controller = AgentController()
        question = input("enter your question: ")
        controller.run(question, user_group=final_user_group)