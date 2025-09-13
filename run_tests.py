import subprocess
import sys

if __name__ == "__main__":
    result = subprocess.run(
        ["uv", "run", "pytest", "--config-file=pyproject.toml"],
        check=True,
    )
    sys.exit(result.returncode)
