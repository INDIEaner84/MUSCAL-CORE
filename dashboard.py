import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))


def dashboard():
    import streamlit as st

    from mcxf_sql import MCXFSQL
    from trace_engine import _TRACE

    st.set_page_config(page_title="MUSCAL Control Dashboard", layout="wide")
    st.title("MUSCAL CONTROL DASHBOARD")

    db_path = st.sidebar.text_input("SQLite DB path", "mcxf.db")
    sql = MCXFSQL(db_path)

    tab1, tab2, tab3 = st.tabs(["MCXF Memory", "RAG Search", "TRACE"])

    with tab1:
        st.subheader("MCXF Memory")
        data = sql.fetch_all()
        st.write(f"**{len(data)} documents**")
        for i, d in enumerate(data):
            with st.expander(f"Document {i}"):
                st.json(d)

    with tab2:
        st.subheader("RAG Search")
        try:
            from simple_rag import SimpleRAG
        except ImportError:
            class SimpleRAG:
                def __init__(self, *a, **kw): pass
                def add(self, text): pass
                def search(self, query): return []
        rag = SimpleRAG()
        for d in sql.fetch_all():
            rag.add(str(d))
        query = st.text_input("Query")
        if query:
            results = rag.search(query)
            for r in results:
                st.write(f"score={r['score']}  {r['text'][:200]}")

    with tab3:
        st.subheader("TRACE")
        events = _TRACE.snapshot()
        st.write(f"**{len(events)} events**")
        for e in events[-50:]:
            st.code(f"[{e.get('trace_level','?')}] {e.get('layer','?')}.{e.get('type','?')} -> {e.get('payload','')}")


if __name__ == "__main__":
    dashboard()
