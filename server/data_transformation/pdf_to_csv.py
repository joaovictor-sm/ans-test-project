import os
import csv
from datetime import datetime
import pdfplumber
import zipfile

# Dicionário de mapeamento de abreviações
COLUMN_MAPPING = {
    "OD": "Seg. Odontológica",
    "AMB": "Seg. Ambulatorial",
}

def replace_abbreviations_in_row(row):
    """Substitui abreviações em todas as células de uma linha"""
    return [COLUMN_MAPPING.get(cell.strip(), cell) if cell else cell for cell in row]

def replace_abbreviations_in_header(headers):
    """Substitui abreviações nos títulos das colunas"""
    return [COLUMN_MAPPING.get(col.strip(), col.strip()) if col else col for col in headers]

def extract_tables_from_pdf(pdf_path):
    """Extrai tabelas do PDF usando pdfplumber"""
    tables = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    # Pular cabeçalhos repetidos
                    if len(tables) > 0 and table[0] == tables[-1][0]:
                        table = table[1:]
                    tables.extend(table)
        return tables
    except Exception as e:
        print(f"Erro ao extrair tabelas: {str(e)}")
        return None

def clean_and_transform_data(table_data):
    """Limpa e transforma os dados extraídos"""
    if not table_data or len(table_data) < 2:
        return None, None
    
    headers = [h.strip() if h else '' for h in table_data[0]]
    clean_data = []
    
    # Substitui abreviações nos títulos das colunas
    headers = replace_abbreviations_in_header(headers)

    for row in table_data[1:]:
        cleaned_row = [cell.strip().replace('\n', ' ') if cell else '' for cell in row]
        clean_data.append(cleaned_row)
    
    return headers, clean_data

def save_to_csv(headers, data, output_path):
    """Salva os dados em arquivo CSV"""
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(headers)
            
            # Aplica a substituição em todas as linhas
            for row in data:
                processed_row = replace_abbreviations_in_row(row)
                writer.writerow(processed_row)
                
        return True
    except Exception as e:
        print(f"Erro ao salvar CSV: {str(e)}")
        return False

def zip_file(csv_path, zip_name):
    """Compacta o arquivo CSV em um arquivo ZIP"""
    try:
        zip_path = csv_path.replace('.csv', f'_{zip_name}.zip')
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(csv_path, os.path.basename(csv_path))
        return zip_path
    except Exception as e:
        print(f"Erro ao compactar o arquivo: {str(e)}")
        return None

def main():
    # Configuração de paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdf_path = os.path.join(base_dir, 'data', 'raw', 'Anexo_I.pdf')
    output_dir = os.path.join(base_dir, 'data', 'processed')
    os.makedirs(output_dir, exist_ok=True)
    
    # Processamento
    print("Extraindo tabelas do PDF...")
    raw_data = extract_tables_from_pdf(pdf_path)
    
    if not raw_data:
        print("Nenhuma tabela encontrada ou erro na extração")
        return

    print("Processando dados...")
    headers, clean_data = clean_and_transform_data(raw_data)
    
    if not headers or not clean_data:
        print("Dados inválidos após transformação")
        return

    # Gerar arquivo CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_filename = f"Rol_de_Procedimentos_{timestamp}.csv"
    csv_path = os.path.join(output_dir, csv_filename)
    
    print("Salvando CSV...")
    if save_to_csv(headers, clean_data, csv_path):
        print(f"CSV salvo em: {csv_path}")
        
        # Compactar CSV em um arquivo ZIP
        zip_name = "Teste_SeuNome"  # Substitua "SeuNome" pelo seu nome
        zip_path = zip_file(csv_path, zip_name)
        
        if zip_path:
            print(f"Arquivo ZIP salvo em: {zip_path}")
        else:
            print("Falha ao compactar o arquivo CSV")
    else:
        print("Falha ao salvar CSV")

if __name__ == "__main__":
    main()
