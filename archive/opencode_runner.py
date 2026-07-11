import subprocess


class OpenCodeRunner:
    def run(self, prompt):
        process = subprocess.Popen(
            ["opencode", "run", prompt],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        out, err = process.communicate()
        return {"stdout": out, "stderr": err, "status": "done"}
