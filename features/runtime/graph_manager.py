import time

SOFT_LIMIT = 500
HARD_LIMIT = 3000
PRUNE_TARGET = 200


class Plugin:
    name = "graph_manager"
    version = "1.0.0"

    def register(self, hooks):
        hooks.setdefault("kernel_after", []).append(self._prune_after)

    def _prune_after(self, ctx):
        kernel = ctx.get("kernel")
        if not kernel:
            return
        g = getattr(kernel, "graph", None)
        if not g:
            return

        count = len(g.nodes)
        if count < SOFT_LIMIT:
            return

        if count >= HARD_LIMIT:
            g.prune_graph()

        if len(g.nodes) <= PRUNE_TARGET:
            return

        self._smart_prune(g)

    def _smart_prune(self, g):
        now = time.time()
        scored = []
        for nid, node in list(g.nodes.items()):
            age = now - getattr(node, "timestamp", now)
            conn_count = sum(
                1 for e in g.edges
                if getattr(e, "source_id", None) == nid or getattr(e, "target_id", None) == nid
            )
            importance = conn_count - age * 0.001
            scored.append((importance, nid, node))

        scored.sort(key=lambda x: x[0])
        to_remove = len(scored) - PRUNE_TARGET
        for _, nid, _ in scored[:to_remove]:
            if hasattr(g, "remove_node"):
                g.remove_node(nid)

    def execute(self, context):
        pass
