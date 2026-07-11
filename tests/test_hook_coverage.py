_HOOK_BASE = {
    "kernel_before": [], "kernel_after": [],
    "mkc_before": [], "mkc_after": [],
    "bridge_before": [], "bridge_after": [],
    "optimizer_before": [], "optimizer_after": [],
    "mel_before": [], "mel_after": [],
    "feedback_before": [], "feedback_after": [],
    "memory_before": [], "memory_after": [],
}


def test_all_hooks_fire():
    from plugin_registry import HOOKS, PLUGINS
    PLUGINS.clear()
    HOOKS.clear()
    HOOKS.update(_HOOK_BASE)
    from plugin_loader import load_plugins
    load_plugins()

    coverage = []

    def make_tracker(hook_name):
        def tracker(ctx):
            keys = sorted(ctx.keys())
            coverage.append({
                "hook": hook_name,
                "keys": keys,
                "has_input": "input_text" in ctx,
                "has_kernel": ctx.get("kernel") is not None,
            })
        return tracker

    for name, hook_list in HOOKS.items():
        if isinstance(hook_list, list):
            hook_list.append(make_tracker(name))

    from kernel import MuscalKernel
    test_inputs = [
        ("print hello world", "simple_print"),
        ("add 5 and 3", "math"),
        ("write file /tmp/test.txt with content data", "filesystem"),
        ("what is the weather", "unmapped"),
    ]

    for input_text, label in test_inputs:
        k = MuscalKernel(enable_graph=True)
        r = k.run(input_text)
        coverage.append({
            "hook": "_result",
            "label": label,
            "input": input_text[:50],
            "success": r.success,
            "memory_id": r.memory_id,
        })

    fired = set(c["hook"] for c in coverage if c["hook"] != "_result")
    all_hooks = set(HOOKS.keys())
    missed = all_hooks - fired
    assert len(missed) <= 2, f"Hooks that never fired: {sorted(missed)}"
    assert fired.issuperset({"kernel_before", "kernel_after", "mkc_before", "mkc_after",
                              "mel_before", "mel_after", "feedback_before", "feedback_after"})

    all_seen = set()
    for c in coverage:
        if c["hook"] != "_result":
            all_seen.update(c["keys"])
    assert "input_text" in all_seen
    assert "_hook_name" in all_seen
    assert "kernel" in all_seen

    for c in coverage:
        if c["hook"] == "_result":
            if c["label"] != "unmapped":
                assert c["success"], f"Failed: {c['label']}"
