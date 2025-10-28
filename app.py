import streamlit as st
import fitz  # PyMuPDF
import io
from PIL import Image
import zipfile


def parse_pages_input(pages_str: str, total_pages: int):
    """Converte entrada tipo "1-3,5" para um conjunto de índices de páginas (base 0)."""
    if not pages_str:
        return set(range(total_pages))
    result = set()
    try:
        for part in pages_str.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                a, b = part.split("-")
                start = max(1, int(a))
                end = min(total_pages, int(b))
                result.update(range(start - 1, end))
            else:
                p = int(part)
                if 1 <= p <= total_pages:
                    result.add(p - 1)
    except Exception:
        # Se parsing falhar, retorna todas as páginas
        return set(range(total_pages))
    return result if result else set(range(total_pages))


def extract_images_from_pdf_bytes(
    file_name: str,
    pdf_bytes: bytes,
    *,
    page_indices: set | None = None,
    output_format: str = "auto",
    jpeg_quality: int = 85,
    deduplicate: bool = True,
):
    """
    Extrai imagens de um PDF fornecido em bytes e retorna lista de
    tuplas (nome_arquivo_imagem, conteudo_em_bytes).
    """
    imagens = []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)
        pages_to_process = page_indices or set(range(total_pages))
        xrefs_processadas = set()

        for pagina_indice in range(total_pages):
            if pagina_indice not in pages_to_process:
                continue
            pagina = doc[pagina_indice]
            lista_imagens = pagina.get_images()

            for indice_img, info_imagem in enumerate(lista_imagens):
                xref = info_imagem[0]
                if deduplicate and xref in xrefs_processadas:
                    continue
                xrefs_processadas.add(xref)

                base_image = doc.extract_image(xref)
                image_bytes = base_image.get("image")
                image_ext = base_image.get("ext", "png")
                if not image_bytes:
                    continue

                # Converte para formato escolhido se necessário
                chosen_ext = image_ext if output_format == "auto" else output_format.lower()
                try:
                    pil_img = Image.open(io.BytesIO(image_bytes))
                    buf = io.BytesIO()
                    save_kwargs = {}
                    if chosen_ext in {"jpg", "jpeg"}:
                        save_kwargs["format"] = "JPEG"
                        save_kwargs["quality"] = jpeg_quality
                        save_kwargs["optimize"] = True
                    elif chosen_ext == "png":
                        save_kwargs["format"] = "PNG"
                    else:
                        save_kwargs["format"] = pil_img.format or "PNG"
                    pil_img.save(buf, **save_kwargs)
                    buf.seek(0)
                    final_bytes = buf.getvalue()
                    final_ext = "jpeg" if save_kwargs.get("format") == "JPEG" else "png" if save_kwargs.get("format") == "PNG" else (pil_img.format or image_ext)
                except Exception:
                    # Se conversão falhar, usa bytes originais
                    final_bytes = image_bytes
                    final_ext = image_ext

                nome_base = file_name[:-4] if file_name.lower().endswith(".pdf") else file_name
                nome_imagem_saida = f"{nome_base}_p{pagina_indice+1}_img{indice_img+1}.{final_ext}"
                imagens.append((nome_imagem_saida, final_bytes))

        doc.close()
    except Exception as e:
        st.error(f"Erro ao processar {file_name}: {e}")

    return imagens


st.set_page_config(page_title="Extrator de Imagens de PDFs", page_icon="🖼️", layout="wide")
# Controle para ocultar cabeçalho após a extração
if "hide_header" not in st.session_state:
    st.session_state["hide_header"] = False
if "images_by_file" not in st.session_state:
    st.session_state["images_by_file"] = {}
if "removed_images" not in st.session_state:
    st.session_state["removed_images"] = set()
if "pending_delete_pdfs" not in st.session_state:
    st.session_state["pending_delete_pdfs"] = set()

# Callbacks para ações imediatas (evitam necessidade de duplo clique)
def _remove_image(image_id: str):
    st.session_state["removed_images"].add(image_id)

def _restore_image(image_id: str):
    st.session_state["removed_images"].discard(image_id)

# Callbacks para exclusão de PDF inteiro
def _mark_pdf_for_delete(fname: str):
    pend = set(st.session_state.get("pending_delete_pdfs", set()))
    pend.add(fname)
    st.session_state["pending_delete_pdfs"] = pend

def _cancel_pdf_delete(fname: str):
    pend = set(st.session_state.get("pending_delete_pdfs", set()))
    if fname in pend:
        pend.remove(fname)
    st.session_state["pending_delete_pdfs"] = pend

def _confirm_pdf_delete(fname: str):
    # Remove do dicionário principal
    base = dict(st.session_state.get("images_by_file", {}))
    if fname in base:
        del base[fname]
    st.session_state["images_by_file"] = base
    # Limpa remoções vinculadas a este arquivo
    removed = set(st.session_state.get("removed_images", set()))
    st.session_state["removed_images"] = {rid for rid in removed if not rid.startswith(f"{fname}:")}
    # Retira pendência
    pend = set(st.session_state.get("pending_delete_pdfs", set()))
    pend.discard(fname)
    st.session_state["pending_delete_pdfs"] = pend

# Moldura suave envolvendo imagem + ações no mesmo bloco
st.markdown(
    """
    <style>
    /* Card para o bloco IMEDIATO dentro da coluna que contém imagem e ações */
    div[data-testid="column"] > div[data-testid="stVerticalBlock"]:has(div[data-testid="stImage"]) {
        border: 1px solid rgba(255,255,255,0.22);
        border-radius: 10px;
        padding: 10px;
        background: rgba(255,255,255,0.04);
        margin-bottom: 10px;
    }
    div[data-testid="column"] > div[data-testid="stVerticalBlock"]:has(div[data-testid="stImage"]):hover {
        border-color: rgba(255,255,255,0.36);
        box-shadow: 0 0 0 2px rgba(255,255,255,0.10) inset;
    }
    /* Ajusta figura interna para não criar espaços extras */
    div[data-testid="stImage"] figure { margin: 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Placeholder para poder remover o cabeçalho dinamicamente
header = st.empty()
if not st.session_state.get("hide_header", False):
    header.title("🖼️ Extrair Imagens de PDFs")
    header.write("Envie um ou mais PDFs, escolha opções e baixe um ZIP com todas as imagens.")

# Sidebar com opções
with st.sidebar:
    st.header("Configurações")
    uploaded_files = st.file_uploader("Arquivos PDF", type=["pdf"], accept_multiple_files=True)
    output_format = st.radio("Formato de saída", ["auto", "png", "jpeg"], index=0, help="Auto mantém formato original quando possível")
    # Qualidade JPEG fixa (removido o controle da UI)
    jpeg_quality = 95
    # Removido controle de páginas na UI; processa todas por padrão
    pages_str = ""
    deduplicate = st.checkbox("Evitar duplicatas (xref)", value=True)
    show_preview = st.checkbox("Mostrar prévia das imagens", value=True)
    start_btn = st.button("Extrair Imagens")

if uploaded_files:
    pass

if uploaded_files and start_btn:
    # Oculta cabeçalho ao iniciar a extração
    st.session_state["hide_header"] = True
    header.empty()
    # Processamento com progresso
    todas_por_arquivo: dict[str, list[tuple[str, bytes]]] = {}
    progress = st.progress(0, text="Iniciando...")
    status = st.empty()
    total = len(uploaded_files)
    for i, uf in enumerate(uploaded_files, start=1):
        status.write(f"Processando: {uf.name} ({i}/{total})")
        pdf_bytes = uf.read()
        # descobrir páginas e converter
        try:
            tmp_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            total_pages = len(tmp_doc)
            tmp_doc.close()
        except Exception:
            total_pages = 1
        page_indices = parse_pages_input(pages_str, total_pages)

        imagens = extract_images_from_pdf_bytes(
            uf.name,
            pdf_bytes,
            page_indices=page_indices,
            output_format=output_format,
            jpeg_quality=jpeg_quality,
            deduplicate=deduplicate,
        )
        todas_por_arquivo[uf.name] = imagens
        progress.progress(i / total, text=f"{int(100 * i / total)}% concluído")

    # Agrega e informa
    total_imgs = sum(len(v) for v in todas_por_arquivo.values())
    if total_imgs:
        st.success(f"Extração concluída. {total_imgs} imagem(ns) encontrada(s) em {len(todas_por_arquivo)} arquivo(s).")

        # Persiste resultado e reseta remoções
        st.session_state["images_by_file"] = todas_por_arquivo
        st.session_state["removed_images"] = set()

        # Exibe por arquivo em abas
        if show_preview:
            tabs = st.tabs(list(st.session_state["images_by_file"].keys()))
            for tab, fname in zip(tabs, st.session_state["images_by_file"].keys()):
                with tab:
                    imgs = st.session_state["images_by_file"][fname]
                    # Barra de título com botão de remoção do PDF
                    hdr_cols = st.columns([0.85, 0.15])
                    hdr_cols[0].markdown(f"**{fname}**")
                    pending = fname in st.session_state.get("pending_delete_pdfs", set())
                    if not pending:
                        hdr_cols[1].button(
                            "❌",
                            key=f"del_pdf_{fname}",
                            help="Remover este PDF e todas as imagens",
                            on_click=_mark_pdf_for_delete,
                            args=(fname,),
                        )
                    else:
                        hdr_cols[1].button(
                            "Cancelar",
                            key=f"cancel_del_{fname}",
                            on_click=_cancel_pdf_delete,
                            args=(fname,),
                        )

                    if pending:
                        st.warning("Remover este PDF e todas as imagens?")
                        st.button(
                            "Confirmar exclusão",
                            key=f"confirm_del_{fname}",
                            type="primary",
                            on_click=_confirm_pdf_delete,
                            args=(fname,),
                        )

                    st.write(f"{len(imgs)} imagem(ns) em {fname}")
                    cols = st.columns(3)
                    for idx, (nome_img, conteudo) in enumerate(imgs):
                        image_id = f"{fname}:{nome_img}"
                        try:
                            slot = cols[idx % 3].container()
                            if image_id in st.session_state["removed_images"]:
                                slot.warning(f"Removida: {nome_img}")
                                slot.button("↩️ Restaurar", key=f"restore_{image_id}", on_click=_restore_image, args=(image_id,))
                            else:
                                img = Image.open(io.BytesIO(conteudo))
                                slot.image(img, caption=nome_img, width="stretch")
                                slot.button("🗑️ Remover", key=f"remove_{image_id}", on_click=_remove_image, args=(image_id,))
                        except Exception:
                            cols[idx % 3].write(f"Não foi possível exibir: {nome_img}")

        # Botão para baixar todas as imagens em um arquivo ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            base_dict = st.session_state.get("images_by_file", todas_por_arquivo)
            removed = st.session_state.get("removed_images", set())
            for fname, imgs in base_dict.items():
                for nome_img, conteudo in imgs:
                    if f"{fname}:{nome_img}" in removed:
                        continue
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

# Renderização persistente de resultados (mantém preview sem nova extração)
if st.session_state.get("images_by_file") and not start_btn:
    base_dict = st.session_state["images_by_file"]
    removed = st.session_state.get("removed_images", set())
    total_imgs = sum(len(v) for v in base_dict.values())
    if total_imgs:
        # Preview
        if show_preview:
            tabs = st.tabs(list(base_dict.keys()))
            for tab, fname in zip(tabs, base_dict.keys()):
                with tab:
                    imgs = base_dict[fname]
                    # Barra de título com botão de remoção do PDF (persistente)
                    hdr_cols = st.columns([0.85, 0.15])
                    hdr_cols[0].markdown(f"**{fname}**")
                    pending = fname in st.session_state.get("pending_delete_pdfs", set())
                    if not pending:
                        hdr_cols[1].button(
                            "❌",
                            key=f"del_pdf_persist_{fname}",
                            help="Remover este PDF e todas as imagens",
                            on_click=_mark_pdf_for_delete,
                            args=(fname,),
                        )
                    else:
                        hdr_cols[1].button(
                            "Cancelar",
                            key=f"cancel_del_persist_{fname}",
                            on_click=_cancel_pdf_delete,
                            args=(fname,),
                        )

                    if pending:
                        st.warning("Remover este PDF e todas as imagens?")
                        st.button(
                            "Confirmar exclusão",
                            key=f"confirm_del_persist_{fname}",
                            type="primary",
                            on_click=_confirm_pdf_delete,
                            args=(fname,),
                        )

                    st.write(f"{len(imgs)} imagem(ns) em {fname}")
                    cols = st.columns(3)
                    for idx, (nome_img, conteudo) in enumerate(imgs):
                        image_id = f"{fname}:{nome_img}"
                        try:
                            slot = cols[idx % 3].container()
                            if image_id in removed:
                                slot.warning(f"Removida: {nome_img}")
                                slot.button("↩️ Restaurar", key=f"restore_persist_{image_id}", on_click=_restore_image, args=(image_id,))
                            else:
                                img = Image.open(io.BytesIO(conteudo))
                                slot.image(img, caption=nome_img, width="stretch")
                                slot.button("🗑️ Remover", key=f"remove_persist_{image_id}", on_click=_remove_image, args=(image_id,))
                        except Exception:
                            cols[idx % 3].write(f"Não foi possível exibir: {nome_img}")

        # ZIP respeitando remoções
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for fname, imgs in base_dict.items():
                for nome_img, conteudo in imgs:
                    if f"{fname}:{nome_img}" in removed:
                        continue
                    zf.writestr(nome_img, conteudo)
        zip_buffer.seek(0)

        st.download_button(
            label="Baixar todas as imagens (ZIP)",
            data=zip_buffer,
            file_name="imagens_extraidas.zip",
            mime="application/zip",
        )

st.caption("Feito com ❤️ usando PyMuPDF (fitz), Pillow e Streamlit")