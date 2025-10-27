import fitz  # PyMuPDF
import os
import io
from PIL import Image

def extrair_imagens_de_pdfs(pasta_pdfs, pasta_saida):
    """
    Extrai todas as imagens de arquivos PDF em uma pasta e as salva em outra pasta.

    Args:
        pasta_pdfs (str): Caminho para a pasta que contém os arquivos PDF.
        pasta_saida (str): Caminho para a pasta onde as imagens extraídas serão salvas.
    """
    
    # 1. Cria a pasta de saída se ela não existir
    os.makedirs(pasta_saida, exist_ok=True)
    
    # 2. Percorre todos os arquivos na pasta de PDFs
    for nome_arquivo in os.listdir(pasta_pdfs):
        if nome_arquivo.lower().endswith(".pdf"):
            caminho_pdf = os.path.join(pasta_pdfs, nome_arquivo)
            print(f"Processando PDF: {nome_arquivo}...")
            
            # Remove a extensão .pdf para usar como parte do nome da imagem
            nome_base = os.path.splitext(nome_arquivo)[0]
            
            try:
                # Abre o documento PDF
                doc = fitz.open(caminho_pdf)
                
                # Armazena XREFs (referências) de imagens já processadas para evitar duplicatas
                xrefs_processadas = set()
                
                for pagina_indice in range(len(doc)):
                    pagina = doc[pagina_indice]
                    
                    # Obtém a lista de imagens na página
                    lista_imagens = pagina.get_images()
                    
                    for indice_img, info_imagem in enumerate(lista_imagens):
                        xref = info_imagem[0] # A XREF é a referência única da imagem no PDF
                        
                        # Verifica se a imagem já foi processada
                        if xref in xrefs_processadas:
                            continue
                        
                        xrefs_processadas.add(xref)
                        
                        # Extrai a imagem
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]
                        
                        # Verifica se os bytes da imagem foram extraídos com sucesso
                        if not image_bytes:
                            continue

                        # Converte os bytes para um objeto PIL Image para manipulação e salvamento
                        try:
                            imagem = Image.open(io.BytesIO(image_bytes))
                            
                            # Cria um nome único para a imagem
                            nome_imagem_saida = f"{nome_base}_p{pagina_indice+1}_img{indice_img+1}.{image_ext}"
                            caminho_imagem_saida = os.path.join(pasta_saida, nome_imagem_saida)
                            
                            # Salva a imagem
                            imagem.save(caminho_imagem_saida)
                            print(f"  -> Imagem salva: {nome_imagem_saida}")
                            
                        except Exception as e:
                            # Captura erros de formato de imagem (raros, mas podem ocorrer)
                            print(f"  -> ERRO ao salvar imagem {xref} do PDF {nome_arquivo}: {e}")

                doc.close()
                print(f"Processamento de {nome_arquivo} concluído.\n")

            except Exception as e:
                print(f"ERRO FATAL ao processar {nome_arquivo}: {e}\n")

# --- Configurações ---
# Usa as pastas do próprio projeto, ao lado deste script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PASTA_DOS_PDFS = os.path.join(BASE_DIR, "PASTA_DOS_PDFS")
PASTA_DE_SAIDA = os.path.join(BASE_DIR, "PASTA_DE_SAIDA")

# Executa a função
extrair_imagens_de_pdfs(PASTA_DOS_PDFS, PASTA_DE_SAIDA)

print("Processo de extração finalizado.")