# extractIMG

Extrator de imagens de PDFs usando PyMuPDF (fitz) e Pillow, com interface web via Streamlit.

## Requisitos
- Python 3.13 (ou 3.9+)
- Dependências: `pymupdf`, `pillow`, `streamlit`

## Instalação
```powershell
C:/Python313/python.exe -m pip install pymupdf pillow streamlit
```

## Execução (Streamlit)
```powershell
C:/Python313/python.exe -m streamlit run app.py --server.port 8501
```
Acesse: `http://localhost:8501`

## Deploy no Streamlit Cloud
1. Garanta que seu repositório no GitHub está atualizado (este projeto já possui `requirements.txt`).
2. Acesse https://share.streamlit.io/ e conecte sua conta ao GitHub.
3. Selecione o repositório `joaomefg/ExtractIMG` e escolha a branch `main`.
4. Em "Main file path", informe `app.py`.
5. (Opcional) Defina a versão do Python como `3.11` nas configurações avançadas.
6. Clique em Deploy.

Observações:
- As dependências necessárias estão em `requirements.txt` (`streamlit`, `pymupdf`, `pillow`).
- O app não grava arquivos no disco; o ZIP é gerado em memória e oferecido para download.
- Se algum PDF for muito grande, o tempo de extração pode aumentar. Streamlit Cloud possui limites de memória/tempo.

## Execução (script local)
O script `main.py` extrai imagens de PDFs presentes em `PASTA_DOS_PDFS` e salva em `PASTA_DE_SAIDA`.
```powershell
C:/Python313/python.exe c:/Users/Smw11/OneDrive/Documentos/ProjetosIaSites/extractIMG/main.py
```

## Publicar no GitHub
1. Inicialize o repositório e faça o primeiro commit:
```powershell
git init
git add .
git commit -m "Inicializa projeto extractIMG"
```
2. Crie um repositório no GitHub (via navegador) e copie a URL `https://github.com/<usuario>/<nome-repo>.git`.
3. Conecte o remoto e publique:
```powershell
git branch -M main
git remote add origin https://github.com/<usuario>/<nome-repo>.git
git push -u origin main
```

> Dica: se usar GitHub CLI, pode criar e publicar com um comando:
```powershell
# requer gh instalado e autenticado
gh repo create <nome-repo> --source . --private --push -y
```

## Observações
- `.gitignore` já exclui `PASTA_DOS_PDFS`, `PASTA_DE_SAIDA`, `__pycache__`, ambientes virtuais e arquivos `.zip`.
- Para desativar telemetria do Streamlit, crie `%userprofile%/.streamlit/config.toml` com:
```
[browser]
gatherUsageStats = false
```