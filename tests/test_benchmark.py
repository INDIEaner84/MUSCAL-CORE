import time

import pytest


def test_benchmark_kernel_run():
    from kernel import MuscalKernel
    k = MuscalKernel(enable_graph=False, enable_sphere=False)

    inputs = [
        "print hello world",
        "add 5 and 3",
        "write file /tmp/bench_test.txt with content benchmark",
    ]

    times = []
    for text in inputs:
        t0 = time.perf_counter()
        result = k.run(text)
        elapsed = time.perf_counter() - t0
        times.append(elapsed)
        assert result.success, f"Failed on: {text}"

    avg = sum(times) / len(times)
    print(f"\nBenchmark: {len(inputs)} runs, avg {avg*1000:.1f}ms, "
          f"min {min(times)*1000:.1f}ms, max {max(times)*1000:.1f}ms")

    assert avg < 5.0, f"Average run time {avg*1000:.1f}ms exceeds 5000ms"


def test_benchmark_plugin_load():
    import plugin_loader
    import plugin_registry

    plugin_registry.PLUGINS.clear()
    plugin_registry.HOOKS.clear()
    plugin_registry.HOOKS.update({
        "kernel_before": [], "kernel_after": [],
        "mkc_before": [], "mkc_after": [],
        "bridge_before": [], "bridge_after": [],
        "optimizer_before": [], "optimizer_after": [],
        "mel_before": [], "mel_after": [],
        "feedback_before": [], "feedback_after": [],
        "memory_before": [], "memory_after": [],
    })

    t0 = time.perf_counter()
    plugin_loader.load_plugins()
    elapsed = time.perf_counter() - t0
    count = len(plugin_registry.PLUGINS)
    print(f"\nLoaded {count} plugins in {elapsed*1000:.1f}ms")
    assert elapsed < 2.0, f"Plugin load {elapsed*1000:.1f}ms exceeds 2000ms"
    assert count >= 8, f"Expected >=8 plugins, got {count}"
