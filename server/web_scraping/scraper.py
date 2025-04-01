import os
import requests
import zipfile
from datetime import datetime

def setup_folders():
    """Cria a estrutura de pastas necessária"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    raw_dir = os.path.join(data_dir, 'raw')
    processed_dir = os.path.join(data_dir, 'processed')
    
    for folder in [data_dir, raw_dir, processed_dir]:
        os.makedirs(folder, exist_ok=True)
    
    return raw_dir, processed_dir

def download_file(url, destination):
    """Baixa um arquivo com tratamento de erros"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Erro ao baixar {url}: {str(e)}")
        return False

def main():
    # URLs dos anexos (versão atualizada 2024)
    ANEXOS = {
        'Anexo_I.pdf': 'https://www.gov.br/ans/pt-br/acesso-a-informacao/participacao-da-sociedade/atualizacao-do-rol-de-procedimentos/Anexo_I_Rol_2021RN_465.2021_RN627L.2024.pdf',
        'Anexo_II.pdf': 'https://www.gov.br/ans/pt-br/acesso-a-informacao/participacao-da-sociedade/atualizacao-do-rol-de-procedimentos/Anexo_II_DUT_2021_RN_465.2021_RN628.2025_RN629.2025.pdf'
    }

    raw_dir, processed_dir = setup_folders()
    downloaded_files = []

    # Download dos arquivos
    for filename, url in ANEXOS.items():
        dest_path = os.path.join(raw_dir, filename)
        print(f"Baixando {filename}...")
        
        if download_file(url, dest_path):
            downloaded_files.append(dest_path)
            print(f"✓ {filename} baixado com sucesso")
        else:
            print(f"✗ Falha no download de {filename}")

    # Compactação
    if downloaded_files:
        zip_filename = os.path.join(processed_dir, f"Anexos_ANS_{datetime.now().strftime('%Y%m%d')}.zip")
        
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for file in downloaded_files:
                zipf.write(file, os.path.basename(file))
        
        print(f"\nArquivos compactados em: {zip_filename}")
        return zip_filename
    else:
        print("\nNenhum arquivo foi baixado para compactação")
        return None

if __name__ == "__main__":
    main()