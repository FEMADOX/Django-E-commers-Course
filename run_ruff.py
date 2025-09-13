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

# if __name__ == "__main__":
#     # Run ruff check
#     check_result = subprocess.run(
#         ["ruff", "check", "."],
#         capture_output=True,
#         check=True,
#     )
#     if check_result.returncode != 0:
#         logger.error("Ruff check failed:")
#         logger.error(check_result.stdout.decode())
#         logger.error(check_result.stderr.decode())
#         sys.exit(check_result.returncode)

#     # Run ruff format
#     format_result = subprocess.run(
#         ["ruff", "format", "."],
#         capture_output=True,
#         check=True,
#     )
#     if format_result.returncode != 0:
#         logger.error("Ruff format failed:")
#         logger.error(format_result.stdout.decode())
#         logger.error(format_result.stderr.decode())
#         sys.exit(format_result.returncode)

#     logger.info("Ruff check and format completed successfully")
#     result = format_result
#     sys.exit(result.returncode)
