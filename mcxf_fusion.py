class MCXFFusionLayer:
    def __init__(self, memory_store, rag, graph=None, sql=None):
        self.memory = memory_store
        self.rag = rag
        self.graph = graph
        self.sql = sql
        self.graph_builder = None
        self.graph_rag = None
        if graph is not None:
            from graph_rag import GraphRAG
            from mcxf_graph_builder import MCXFGraphBuilder
            self.graph_builder = MCXFGraphBuilder(graph)
            self.graph_rag = GraphRAG(graph)

    def ingest(self, mcxf_doc):
        self.memory.add(mcxf_doc)
        flat = str(mcxf_doc)
        self.rag.add(flat)
        if self.graph_builder:
            self.graph_builder.ingest(mcxf_doc)
        if self.sql:
            self.sql.insert(mcxf_doc)

    def retrieve_context(self, query):
        ctx = {
            "cosine": self.rag.search(query),
            "graph": [],
        }
        if self.graph_rag:
            ctx["graph"] = self.graph_rag.retrieve(query)
        return ctx


_module_fusion = None


def get_fusion_layer():
    return _module_fusion


def init_fusion(memory_store=None, rag=None, graph=None, sql_path=None):
    global _module_fusion
    if _module_fusion is not None:
        return
    from mcxf_memory_store import MCXFMemoryStore
    from simple_rag import SimpleRAG
    ms = memory_store or MCXFMemoryStore()
    r = rag or SimpleRAG()
    sql = None
    if sql_path:
        from mcxf_sql import MCXFSQL
        sql = MCXFSQL(sql_path)
    _module_fusion = MCXFFusionLayer(ms, r, graph=graph, sql=sql)


def store_mcxf(mcxf):
    if _module_fusion is None:
        init_fusion()
    _module_fusion.ingest(mcxf)


def get_memory_context(query):
    if _module_fusion is None:
        init_fusion()
    return _module_fusion.retrieve_context(query)
