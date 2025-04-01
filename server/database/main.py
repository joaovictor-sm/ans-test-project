from database.config import engine
from database.models import Base
from database.download import download_operadoras, download_demonstracoes, import_data
from database.queries import get_top_operadoras_trimestre, get_top_operadoras_ano

def create_tables():
    """Cria a estrutura do banco de dados"""
    Base.metadata.create_all(engine)
    print("✓ Tabelas criadas com sucesso")

def main():
    print("Iniciando processo do teste...\n")
    
    # 1. Baixar arquivos
    print("1. Baixando dados...")
    if not download_operadoras():
        print("\n⚠️ Falha ao baixar operadoras")
        return
    
    if not download_demonstracoes():
        print("\n⚠️ Falha ao baixar demonstrações")
    
    # 2. Criar tabelas
    print("\n2. Criando estrutura do banco...")
    create_tables()
    
    # 3. Importar dados
    print("\n3. Importando dados...")
    if not import_data():
        print("\n⚠️ Falha ao importar dados")
    
    # 4. Executar queries
    print("\n4. Resultados das queries:")
    
    print("\nTop 10 operadoras - último trimestre:")
    results = get_top_operadoras_trimestre()
    if results:
        for op in results:
            print(f"- {op.razao_social}: R${op.total:,.2f}")
    else:
        print("Nenhum resultado encontrado")
    
    print("\nTop 10 operadoras - último ano:")
    results = get_top_operadoras_ano()
    if results:
        for op in results:
            print(f"- {op.razao_social}: R${op.total:,.2f}")
    else:
        print("Nenhum resultado encontrado")

if __name__ == "__main__":
    main()