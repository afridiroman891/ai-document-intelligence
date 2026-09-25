import os
from datetime import datetime

import pandas as pd
import streamlit as st

from database import (
    init_db, get_by_hash, create_document, list_documents,
    get_document, update_status, delete_document
)
from storage import validate_file, calculate_sha256, save_file, delete_file
from processor import process_document

st.set_page_config(
    page_title="AI Document Intelligence",
    page_icon="📄",
    layout="wide"
)

init_db()

st.title("📄 AI Document Intelligence")
st.caption("Week 4 — Document Repository, Search, Filtering & Duplicate Detection")

# Sidebar upload
with st.sidebar:
    st.header("Upload Document")
    uploaded = st.file_uploader(
        "Choose a document",
        type=["pdf", "png", "jpg", "jpeg", "txt"]
    )

    if uploaded is not None:
        if st.button("Process & Store", type="primary", use_container_width=True):
            data = uploaded.getvalue()
            valid, error = validate_file(uploaded.name, len(data))

            if not valid:
                st.error(error)
            else:
                file_hash = calculate_sha256(data)
                duplicate = get_by_hash(file_hash)

                if duplicate:
                    st.warning("Duplicate detected. This file is already stored.")
                    st.info(
                        f"Existing document #{duplicate['id']}: "
                        f"{duplicate['original_filename']}"
                    )
                    st.session_state["selected_id"] = duplicate["id"]
                else:
                    with st.spinner("Reading, classifying and extracting..."):
                        try:
                            result = process_document(data, uploaded.name)
                            path, stored_name = save_file(
                                data, uploaded.name, result["document_type"]
                            )

                            doc_id = create_document({
                                "original_filename": uploaded.name,
                                "stored_filename": stored_name,
                                "document_type": result["document_type"],
                                "upload_date": datetime.now().isoformat(timespec="seconds"),
                                "company": result["company"],
                                "invoice_number": result["invoice_number"],
                                "total_amount": result["total_amount"],
                                "file_path": str(path),
                                "text_preview": result["text"][:1000],
                                "file_hash": file_hash,
                                "status": result["status"]
                            })
                            st.success(f"Document stored successfully. ID: {doc_id}")
                            st.session_state["selected_id"] = doc_id
                            st.rerun()
                        except Exception:
                            st.error(
                                "The document could not be processed. "
                                "Please verify that the file is readable."
                            )

    st.divider()
    st.info("Maximum upload size: 10 MB")

# Search/filter controls
st.subheader("🔎 Search & Filter")

c1, c2, c3 = st.columns(3)
with c1:
    search = st.text_input(
        "Search",
        placeholder="Filename, company, invoice number, type, text..."
    )
with c2:
    document_type = st.selectbox(
        "Document type", ["All", "Invoice", "Resume", "Other"]
    )
with c3:
    status = st.selectbox(
        "Processing status", ["All", "Processed", "Needs Review", "Failed"]
    )

c4, c5, c6 = st.columns(3)
with c4:
    date_from = st.date_input("From date", value=None)
with c5:
    date_to = st.date_input("To date", value=None)
with c6:
    sort_order = st.selectbox("Sort", ["Newest", "Oldest"])

if st.button("Clear Filters"):
    st.rerun()

rows = list_documents(
    search=search,
    document_type=document_type,
    status=status,
    date_from=str(date_from) if date_from else "",
    date_to=str(date_to) if date_to else "",
    sort_order=sort_order
)

st.write(f"**{len(rows)} document(s) found**")

if rows:
    display_rows = []
    for row in rows:
        display_rows.append({
            "ID": row["id"],
            "Filename": row["original_filename"],
            "Type": row["document_type"],
            "Company": row["company"] or "",
            "Invoice #": row["invoice_number"] or "",
            "Total": row["total_amount"] if row["total_amount"] is not None else "",
            "Status": row["status"],
            "Uploaded": row["upload_date"]
        })

    st.dataframe(
        pd.DataFrame(display_rows),
        use_container_width=True,
        hide_index=True
    )

    ids = [row["id"] for row in rows]
    selected = st.selectbox(
        "Select a document for details",
        ids,
        format_func=lambda x: f"#{x} — {next(r['original_filename'] for r in rows if r['id'] == x)}"
    )
    st.session_state["selected_id"] = selected
else:
    st.info("No documents match the current search/filter settings.")

# Detail view
selected_id = st.session_state.get("selected_id")
if selected_id:
    doc = get_document(selected_id)

    if doc:
        st.divider()
        st.subheader(f"📋 Document Detail — #{doc['id']}")

        a, b, c = st.columns(3)
        a.metric("Type", doc["document_type"])
        b.metric("Status", doc["status"])
        c.metric(
            "Total Amount",
            str(doc["total_amount"]) if doc["total_amount"] is not None else "—"
        )

        left, right = st.columns(2)

        with left:
            st.write("**Original filename:**", doc["original_filename"])
            st.write("**Stored filename:**", doc["stored_filename"])
            st.write("**Upload date:**", doc["upload_date"])
            st.write("**Company:**", doc["company"] or "—")
            st.write("**Invoice number:**", doc["invoice_number"] or "—")

        with right:
            st.write("**File path:**", doc["file_path"])
            st.write("**SHA-256:**")
            st.code(doc["file_hash"])

        st.write("**Text preview**")
        st.text_area(
            "Extracted text",
            doc["text_preview"] or "No text extracted.",
            height=180,
            label_visibility="collapsed"
        )

        action1, action2, action3 = st.columns(3)

        with action1:
            if os.path.exists(doc["file_path"]):
                with open(doc["file_path"], "rb") as f:
                    st.download_button(
                        "⬇️ Download File",
                        data=f.read(),
                        file_name=doc["original_filename"],
                        use_container_width=True
                    )
            else:
                st.warning("Stored file is missing.")

        with action2:
            new_status = st.selectbox(
                "Change status",
                ["Processed", "Needs Review", "Failed"],
                index=["Processed", "Needs Review", "Failed"].index(doc["status"])
            )
            if st.button("Update Status", use_container_width=True):
                update_status(doc["id"], new_status)
                st.success("Status updated.")
                st.rerun()

        with action3:
            if st.button("🗑️ Delete Document", use_container_width=True):
                path = doc["file_path"]
                delete_document(doc["id"])
                delete_file(path)
                st.session_state.pop("selected_id", None)
                st.success("Document deleted.")
                st.rerun()

st.divider()
st.caption("AI Document Intelligence • Week 4 Repository Layer")
