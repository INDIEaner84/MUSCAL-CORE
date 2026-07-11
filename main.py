import os


def main():
    os.makedirs("storage", exist_ok=True)
    from runtime.monitoring.logging import setup_logging
    setup_logging()

    from plugin_loader import load_plugins
    load_plugins()

    from kernel import MuscalKernel
    kernel = MuscalKernel(enable_graph=True, enable_sphere=True)

    while True:
        user_input = input(">>> ")
        result = kernel.run(user_input)

        print("PLAN   :", result.execution_plan.intent if result.execution_plan else "N/A")
        print("RESULT :", result.execution)
        print("MEMORY :", result.memory_id)

        if not result.success:
            print("ERRORS :", result.errors)

        if result.feedback.summary != "no issues detected":
            print("FEEDBACK:", result.feedback.summary)

        snap = kernel.sphere.get_snapshot() if kernel.sphere else {}
        if snap:
            rings = snap["rings"]
            print(f"SPHERE : {len(rings['inner'])}i/{len(rings['middle'])}m/{len(rings['outer'])}o"
                  f" | focus: {snap['center']['id'] if snap['center'] else '-'}"
                  f" | path: {len(snap['active_path'])} steps")


if __name__ == "__main__":
    main()
