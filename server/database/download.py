import os
import requests
import csv
import zipfile
import io
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from sqlalchemy import func
from .config import SessionLocal
from .models import Operadora, Demonstracao

# Configurações de diretório
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'server', 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# URLs base
BASE_URL = "https://dadosabertos.ans.gov.br/FTP/PDA/"
OPERADORAS_URL = urljoin(BASE_URL, "operadoras_de_plano_de_saude_ativas/")
DEMONSTRACOES_URL = urljoin(BASE_URL, "demonstracoes_contabeis/")

def download_operadoras():
    """Baixa o arquivo de operadoras"""
    print("Baixando dados de operadoras...")
    try:
        # URL verificada em 10/06/2024
        url = urljoin(OPERADORAS_URL, "Relatorio_cadop.csv")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Verifica se é realmente um CSV
        if '<html>' in response.text.lower():
            raise ValueError("Servidor retornou HTML em vez de CSV")
            
        file_path = os.path.join(DATA_DIR, "operadoras.csv")
        with open(file_path, 'wb') as f:
            f.write(response.content)
        print("✓ Operadoras baixadas com sucesso")
        return True
    except Exception as e:
        print(f"✗ Erro ao baixar operadoras: {str(e)}")
        return False

def download_demonstracoes():
    """Baixa demonstrações contábeis"""
    print("Baixando demonstrações contábeis...")
    
    # Obtém anos disponíveis
    try:
        years = []
        response = requests.get(DEMONSTRACOES_URL, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and href.endswith('/') and href[:-1].isdigit():
                years.append(int(href[:-1]))
        years = sorted(years, reverse=True)[:2]  # Pega os 2 anos mais recentes
    except Exception as e:
        print(f"✗ Erro ao obter anos disponíveis: {str(e)}")
        return False
    
    success = True
    for year in years:
        try:
            year_url = urljoin(DEMONSTRACOES_URL, f"{year}/")
            response = requests.get(year_url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Procura por arquivos CSV ou ZIP
            for link in soup.find_all('a'):
                href = link.get('href')
                if href and (href.lower().endswith('.csv') or href.lower().endswith('.zip')):
                    file_url = urljoin(year_url, href)
                    os.makedirs(os.path.join(DATA_DIR, "demonstracoes", str(year)), exist_ok=True)
                    
                    if href.lower().endswith('.zip'):
                        # Processa arquivo ZIP
                        response = requests.get(file_url, stream=True)
                        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
                            zip_ref.extractall(os.path.join(DATA_DIR, "demonstracoes", str(year)))
                        print(f"✓ Demonstrações {year} (ZIP) baixadas e extraídas")
                    else:
                        # Processa arquivo CSV diretamente
                        response = requests.get(file_url, stream=True)
                        file_path = os.path.join(DATA_DIR, "demonstracoes", str(year), "demonstracoes.csv")
                        with open(file_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        print(f"✓ Demonstrações {year} (CSV) baixadas")
                    break
            else:
                print(f"✗ Nenhum arquivo válido encontrado para {year}")
                success = False
        except Exception as e:
            print(f"✗ Erro ao processar ano {year}: {str(e)}")
            success = False
    
    return success

def import_data():
    """Importa todos os dados para o banco de dados com foco em performance e robustez"""
    print("Importando dados...")
    
    # Mapeamento de colunas atualizado com mais alternativas
    COLUMN_MAPS = {
        'operadoras': {
            'registro_ans': ['Registro_ANS', 'Registro ANS', 'CD_OPERADORA', 'Número da ANS', 'NR_REGISTRO'],
            'cnpj': ['CNPJ', 'nr_cnpj', 'CNPJ da Operadora', 'NR_CNPJ'],
            'razao_social': ['Razao_Social', 'Razão Social', 'NM_RAZAO_SOCIAL', 'Razão Social', 'NM_OPERADORA']
        },
        'demonstracoes': {
            'registro_ans': ['Registro_ANS', 'Registro ANS', 'CD_OPERADORA', 'Número da ANS'],
            'descricao': ['Descricao', 'Descrição', 'DS_CONTA', 'Conta Contábil', 'DS_DESCRICAO'],
            'valor': ['Valor', 'VL_SALDO_FINAL', 'Saldo Final', 'Valor R$', 'VL_VALOR'],
            'data': ['Data', 'DT_COMPETENCIA', 'Competência', 'Ano/Mês', 'DT_REFERENCIA']
        }
    }

    # 1. Importação Otimizada de Operadoras
    def import_operadoras(db):
        operadoras_path = os.path.join(DATA_DIR, "operadoras.csv")
        if not os.path.exists(operadoras_path):
            print("✗ Arquivo de operadoras não encontrado")
            return False, 0, 0

        with open(operadoras_path, 'r', encoding='latin1') as f:
            # Detecção automática de formato
            sample = f.read(4096)
            f.seek(0)
            
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample)
            has_header = sniffer.has_header(sample)
            
            reader = csv.DictReader(f, dialect=dialect) if has_header else csv.DictReader(f, fieldnames=None)
            
            # Mapeamento dinâmico de colunas
            mapped_fields = {}
            for field, alternatives in COLUMN_MAPS['operadoras'].items():
                for alt in alternatives:
                    if alt in reader.fieldnames:
                        mapped_fields[field] = alt
                        break
                else:
                    print(f"✗ Coluna para '{field}' não encontrada")
                    return False, 0, 0

            # Importação em lote para melhor performance
            batch_size = 1000
            batch = []
            operadoras_count = 0
            errors = 0
            
            for row in reader:
                try:
                    registro = row[mapped_fields['registro_ans']].strip()
                    cnpj = row[mapped_fields['cnpj']].strip()
                    razao = row[mapped_fields['razao_social']].strip()
                    
                    if not registro or not cnpj or not razao:
                        raise ValueError("Dados incompletos")
                    
                    batch.append({
                        'registro_ans': registro,
                        'cnpj': cnpj,
                        'razao_social': razao
                    })
                    
                    if len(batch) >= batch_size:
                        db.bulk_insert_mappings(Operadora, batch)
                        operadoras_count += len(batch)
                        batch = []
                        
                except Exception as e:
                    errors += 1
                    if errors <= 5:
                        print(f"Erro na linha {reader.line_num}: {str(e)}")
            
            # Insere o restante
            if batch:
                db.bulk_insert_mappings(Operadora, batch)
                operadoras_count += len(batch)
            
            return True, operadoras_count, errors

    # 2. Importação Avançada de Demonstrações
    def import_demonstracoes(db):
        demonstracao_files = []
        demonstracoes_dir = os.path.join(DATA_DIR, "demonstracoes")
        
        if os.path.exists(demonstracoes_dir):
            for root, _, files in os.walk(demonstracoes_dir):
                for file in files:
                    if file.lower().endswith('.csv'):
                        demonstracao_files.append(os.path.join(root, file))
        
        if not demonstracao_files:
            print("✗ Nenhum arquivo de demonstrações encontrado")
            return False, 0, 0

        demonstracoes_count = 0
        errors = 0
        
        for csv_path in demonstracao_files:
            try:
                with open(csv_path, 'r', encoding='latin1') as f:
                    # Detecção inteligente de formato
                    sample = f.read(4096)
                    f.seek(0)
                    
                    sniffer = csv.Sniffer()
                    dialect = sniffer.sniff(sample)
                    has_header = sniffer.has_header(sample)
                    
                    reader = csv.DictReader(f, dialect=dialect) if has_header else csv.DictReader(f, fieldnames=None)
                    
                    # Mapeamento flexível de colunas
                    mapped_fields = {}
                    for field, alternatives in COLUMN_MAPS['demonstracoes'].items():
                        for alt in alternatives:
                            if alt in reader.fieldnames:
                                mapped_fields[field] = alt
                                break
                    
                    required_fields = ['registro_ans', 'descricao', 'valor']
                    if not all(f in mapped_fields for f in required_fields):
                        print(f"✗ Campos obrigatórios não encontrados em {csv_path}")
                        continue
                    
                    # Filtro para eventos relevantes
                    target_desc = "EVENTOS/ SINISTROS CONHECIDOS OU AVISADOS DE ASSISTÊNCIA A SAÚDE MEDICO HOSPITALAR"
                    
                    # Importação em lote
                    batch = []
                    batch_size = 1000
                    
                    for row in reader:
                        try:
                            descricao = row[mapped_fields['descricao']].strip().upper()
                            if target_desc not in descricao:
                                continue
                            
                            registro = row[mapped_fields['registro_ans']].strip()
                            valor_str = row[mapped_fields['valor']].strip()
                            
                            if not registro or not valor_str:
                                continue
                            
                            # Conversão robusta de valores
                            try:
                                valor = float(valor_str.replace('.', '').replace(',', '.'))
                            except:
                                try:
                                    valor = float(valor_str.replace(',', ''))
                                except:
                                    raise ValueError(f"Valor inválido: {valor_str}")
                            
                            # Determinação do período
                            trimestre, ano = 1, datetime.now().year
                            if 'data' in mapped_fields and mapped_fields['data'] in row:
                                data_str = row[mapped_fields['data']].strip()
                                if data_str:
                                    try:
                                        # Tenta múltiplos formatos de data
                                        for fmt in ('%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d', '%Y%m%d'):
                                            try:
                                                data = datetime.strptime(data_str, fmt).date()
                                                trimestre = (data.month - 1) // 3 + 1
                                                ano = data.year
                                                break
                                            except:
                                                continue
                                    except:
                                        pass
                            
                            batch.append({
                                'registro_ans': registro,
                                'descricao': descricao,
                                'valor': valor,
                                'trimestre': trimestre,
                                'ano': ano
                            })
                            
                            if len(batch) >= batch_size:
                                db.bulk_insert_mappings(Demonstracao, batch)
                                demonstracoes_count += len(batch)
                                batch = []
                                
                        except Exception as e:
                            errors += 1
                            if errors <= 5:
                                print(f"Erro na linha {reader.line_num}: {str(e)}")
                    
                    # Insere o restante
                    if batch:
                        db.bulk_insert_mappings(Demonstracao, batch)
                        demonstracoes_count += len(batch)
                        
            except Exception as e:
                print(f"✗ Erro ao processar arquivo {csv_path}: {str(e)}")
                errors += 1
        
        return True, demonstracoes_count, errors

    db = SessionLocal()
    try:
        # Importação de operadoras
        success_op, op_count, op_errors = import_operadoras(db)
        if success_op:
            print(f"✓ {op_count} operadoras importadas com sucesso")
            print(f"✗ {op_errors} registros de operadoras com problemas")
        
        # Importação de demonstrações
        success_dem, dem_count, dem_errors = import_demonstracoes(db)
        if success_dem:
            print(f"✓ {dem_count} demonstrações importadas com sucesso")
            print(f"✗ {dem_errors} registros de demonstrações com problemas")
        
        # Análises após importação
        if success_op and success_dem:
            run_analytics(db)
        
        db.commit()
        return success_op and success_dem
        
    except Exception as e:
        db.rollback()
        print(f"✗ Erro crítico durante a importação: {str(e)}")
        return False
    finally:
        db.close()

def run_analytics(db):
    """Executa análises avançadas nos dados importados"""
    print("\nExecutando análises...")
    
    # 1. Análise do último trimestre completo
    current_date = datetime.now()
    current_year = current_date.year
    current_quarter = (current_date.month - 1) // 3 + 1
    
    # Ajusta para o último trimestre completo (pode estar no meio do trimestre atual)
    last_complete_quarter = current_quarter - 1 if current_date.month % 3 != 0 else current_quarter
    last_complete_year = current_year if last_complete_quarter > 0 else current_year - 1
    last_complete_quarter = last_complete_quarter if last_complete_quarter > 0 else 4
    
    print(f"\nTop 10 operadoras - {last_complete_quarter}° trimestre de {last_complete_year}:")
    
    top_operadoras_trimestre = db.query(
        Operadora.razao_social,
        Operadora.cnpj,
        Demonstracao.registro_ans,
        Demonstracao.valor
    ).join(
        Demonstracao, Operadora.registro_ans == Demonstracao.registro_ans
    ).filter(
        Demonstracao.ano == last_complete_year,
        Demonstracao.trimestre == last_complete_quarter,
        Demonstracao.descricao.like("%EVENTOS/ SINISTROS CONHECIDOS OU AVISADOS DE ASSISTÊNCIA A SAÚDE MEDICO HOSPITALAR%")
    ).order_by(
        Demonstracao.valor.desc()
    ).limit(10).all()
    
    if top_operadoras_trimestre:
        for i, (razao, cnpj, registro, valor) in enumerate(top_operadoras_trimestre, 1):
            print(f"{i}. {razao} (ANS: {registro}, CNPJ: {cnpj}) - R$ {valor:,.2f}")
        
        # Análise adicional: total do trimestre
        total_trimestre = sum([item[3] for item in top_operadoras_trimestre])
        print(f"\nTotal gasto pelas top 10: R$ {total_trimestre:,.2f}")
        print(f"Média por operadora: R$ {total_trimestre/10:,.2f}")
    else:
        print("Nenhum dado disponível para o período")
    
    # 2. Análise do último ano completo
    last_complete_year = current_year if current_date.month == 1 and current_date.day == 1 else current_year - 1
    
    print(f"\nTop 10 operadoras - Ano {last_complete_year}:")
    
    top_operadoras_ano = db.query(
        Operadora.razao_social,
        Operadora.cnpj,
        Demonstracao.registro_ans,
        func.sum(Demonstracao.valor).label('total')
    ).join(
        Demonstracao, Operadora.registro_ans == Demonstracao.registro_ans
    ).filter(
        Demonstracao.ano == last_complete_year,
        Demonstracao.descricao.like("%EVENTOS/ SINISTROS CONHECIDOS OU AVISADOS DE ASSISTÊNCIA A SAÚDE MEDICO HOSPITALAR%")
    ).group_by(
        Operadora.razao_social,
        Operadora.cnpj,
        Demonstracao.registro_ans
    ).order_by(
        func.sum(Demonstracao.valor).desc()
    ).limit(10).all()
    
    if top_operadoras_ano:
        for i, (razao, cnpj, registro, total) in enumerate(top_operadoras_ano, 1):
            print(f"{i}. {razao} (ANS: {registro}, CNPJ: {cnpj}) - R$ {total:,.2f}")
        
        # Análise adicional: variação percentual
        if top_operadoras_trimestre and len(top_operadoras_ano) >= 4:
            print("\nAnálise de variação trimestral:")
            for i, (razao, _, registro, _) in enumerate(top_operadoras_ano[:4], 1):
                trim_data = next((item for item in top_operadoras_trimestre if item[2] == registro), None)
                if trim_data:
                    percent = (trim_data[3] / (total/4)) * 100
                    print(f"{i}. {razao}: {percent:.1f}% da média trimestral anual")
    else:
        print("Nenhum dado disponível para o período")
    
    # 3. Análise de crescimento anual
    if last_complete_year > 2020:  # Garante que temos pelo menos 2 anos para comparação
        print("\nAnálise de crescimento anual:")
        
        # Pega os totais dos últimos 2 anos
        anos_analise = [last_complete_year - 1, last_complete_year] if last_complete_year > 2020 else [2020, 2021]
        
        totais_anos = []
        for ano in anos_analise:
            total_ano = db.query(
                func.sum(Demonstracao.valor)
            ).filter(
                Demonstracao.ano == ano,
                Demonstracao.descricao.like("%EVENTOS/ SINISTROS CONHECIDOS OU AVISADOS DE ASSISTÊNCIA A SAÚDE MEDICO HOSPITALAR%")
            ).scalar() or 0
            
            totais_anos.append(total_ano)
        
        if totais_anos[1] > 0 and totais_anos[0] > 0:
            crescimento = ((totais_anos[1] - totais_anos[0]) / totais_anos[0]) * 100
            print(f"Crescimento de {crescimento:.2f}% de {anos_analise[0]} para {anos_analise[1]}")
            print(f"Total {anos_analise[0]}: R$ {totais_anos[0]:,.2f}")
            print(f"Total {anos_analise[1]}: R$ {totais_anos[1]:,.2f}")