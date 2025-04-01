from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})

try:
    with engine.connect() as conn:
        print("Conexão bem-sucedida! 🎉")
except Exception as e:
    print("Erro ao conectar:", e)
