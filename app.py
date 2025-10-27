import streamlit as st
import fitz  # PyMuPDF
import io
from PIL import Image
import zipfile


def extract_images_from_pdf_bytes(file_name: str, pdf_bytes: bytes):
    """
    Extrai imagens de um PDF fornecido em bytes e retorna uma lista de
    tuplas (nome_arquivo_imagem, conteudo_em_bytes).
    """
    imagens = []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        xrefs_processadas = set()

        for pagina_indice in range(len(doc)):
            pagina = doc[pagina_indice]
            lista_imagens = pagina.get_images()

            for indice_img, info_imagem in enumerate(lista_imagens):
                xref = info_imagem[0]
                if xref in xrefs_processadas:
                    continue
                xrefs_processadas.add(xref)

                base_image = doc.extract_image(xref)
                image_bytes = base_image.get("image")
                image_ext = base_image.get("ext", "png")
                if not image_bytes:
                    continue

                nome_base = file_name[:-4] if file_name.lower().endswith(".pdf") else file_name
                nome_imagem_saida = f"{nome_base}_p{pagina_indice+1}_img{indice_img+1}.{image_ext}"
                imagens.append((nome_imagem_saida, image_bytes))

        doc.close()
    except Exception as e:
        st.error(f"Erro ao processar {file_name}: {e}")

    return imagens


st.set_page_config(page_title="Extrator de Imagens de PDFs", page_icon="🖼️", layout="wide")
st.title("Extrair Imagens de PDFs")
st.write("Envie um ou mais arquivos PDF e extraia todas as imagens contidas neles.")

uploaded_files = st.file_uploader("Selecione arquivos PDF", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    if st.button("Extrair Imagens"):
        todas_imagens = []
        with st.spinner("Extraindo imagens dos PDFs enviados..."):
            for uf in uploaded_files:
                # Lê todos os bytes do arquivo enviado
                pdf_bytes = uf.read()
                imagens = extract_images_from_pdf_bytes(uf.name, pdf_bytes)
                todas_imagens.extend(imagens)

        if todas_imagens:
            st.success(f"Extração concluída. {len(todas_imagens)} imagem(ns) encontrada(s).")

            # Exibe imagens em grade
            cols = st.columns(3)
            for idx, (nome_img, conteudo) in enumerate(todas_imagens):
                try:
                    img = Image.open(io.BytesIO(conteudo))
                    cols[idx % 3].image(img, caption=nome_img, use_column_width=True)
                except Exception:
                    cols[idx % 3].write(f"Imagem não exibível: {nome_img}")

            # Botão para baixar todas as imagens em um arquivo ZIP
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for nome_img, conteudo in todas_imagens:
                    zf.writestr(nome_img, conteudo)
            zip_buffer.seek(0)

            st.download_button(
                label="Baixar todas as imagens (ZIP)",
                data=zip_buffer,
                file_name="imagens_extraidas.zip",
                mime="application/zip",
            )
        else:
            st.warning("Nenhuma imagem foi encontrada nos PDFs enviados.")

st.caption("Powered by PyMuPDF (fitz) e Pillow")