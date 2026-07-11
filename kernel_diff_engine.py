class KernelDiffEngine:
    def diff(self, before: dict, after: dict):
        changes = []
        keys = set(before.keys()).union(set(after.keys()))
        for k in keys:
            b = before.get(k)
            a = after.get(k)
            if b != a:
                changes.append({
                    "field": k,
                    "before": b,
                    "after": a,
                    "type": self._classify_change(b, a),
                })
        return {"change_count": len(changes), "changes": changes}

    def _classify_change(self, before, after):
        if before is None:
            return "ADD"
        if after is None:
            return "DELETE"
        return "MODIFY"


class StateStore:
    def __init__(self):
        self.snapshots = {}

    def save(self, run_id: str, mcxf_state: dict):
        if run_id not in self.snapshots:
            self.snapshots[run_id] = []
        self.snapshots[run_id].append(mcxf_state)

    def get(self, run_id: str):
        return self.snapshots.get(run_id, [])


class ReplayEngine:
    def replay(self, snapshots: list):
        print("\n=== MUSCAL REPLAY START ===")
        for i, state in enumerate(snapshots):
            print(f"\n--- STEP {i} ---")
            print("MCXF STATE:")
            print(state)
        print("\n=== REPLAY END ===")


def link_trace_to_state(trace, state_store, run_id):
    return {
        "trace_length": len(trace),
        "state_snapshots": len(state_store.get(run_id)),
    }
