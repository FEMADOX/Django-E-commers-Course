import logging
import subprocess
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_ruff() -> int:
    """Run ruff with detailed output"""
    logger.info("🧹 Running Ruff linting...")
    logger.info("=" * 50)

    try:
        # Check linting
        logger.info("📋 Checking code style...")
        subprocess.run(
            [
                "uv",
                "run",
                "ruff",
                "check",
                ".",
                "--show-fixes",  # Show available fixes
            ],
            check=True,
            text=True,
            capture_output=False,
        )

        # Check formatting
        logger.info("📝 Checking code formatting...")
        subprocess.run(
            [
                "uv",
                "run",
                "ruff",
                "format",
                "--check",
                ".",
            ],
            check=True,
            text=True,
            capture_output=False,
        )

        logger.info("✅ All linting checks passed!")
        return 0

    except subprocess.CalledProcessError as e:
        logger.info(f"❌ Linting failed with exit code: {e.returncode}")
        logger.info("💡 Try running: uv run ruff check --fix .")
        return e.returncode
    except Exception as e:  # noqa: BLE001
        logger.info(f"💥 Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = run_ruff()
    sys.exit(exit_code)
