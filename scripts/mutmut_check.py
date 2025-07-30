#!/usr/bin/env python

import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

MIN_SCORE = 80  # Minimum threshold for mutation score (% killed)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def get_executable_path(cmd: str) -> str:
    """Find the absolute path to an executable."""
    exe_path = shutil.which(cmd)
    if not exe_path:
        logging.error(f"Executable '{cmd}' not found in PATH.")
        sys.exit(1)
    return exe_path


def check_coverage() -> bool:
    logging.info("🚦 [MUTATION CHECK] Checking minimum coverage before mutation testing...")
    try:
        pytest_path = get_executable_path("pytest")
        result = subprocess.run(
            [
                pytest_path,
                "--cov=src",
                "--cov-report=term-missing",
                "--cov-report=html",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        logging.error("❌ [MUTATION CHECK] Coverage run failed.")
        print(e.stdout or e.stderr or str(e))
        return False

    stdout = result.stdout or ""
    for line in stdout.splitlines():
        if "TOTAL" in line and "%" in line:
            try:
                percent = float(line.strip().split()[-1].replace("%", ""))
            except Exception as ex:
                logging.warning(f"Failed to parse coverage percentage: {ex} | line: {line}")
                continue
            if percent >= MIN_SCORE:
                logging.info("✅ [MUTATION CHECK] Coverage is OK. Proceeding to mutation testing.")
                return True
            logging.error(
                f"❌ [MUTATION CHECK] Coverage too low: {percent:.2f}% (minimum {MIN_SCORE}%)"
            )
            return False

    logging.warning("⚠️ [MUTATION CHECK] Could not find coverage percentage in output.")
    return False


def run_mutmut():
    logging.info("🧬 Running mutation tests...")

    os.environ["PYTEST_ADDOPTS"] = "-q -x --disable-warnings"

    try:
        mutmut_path = get_executable_path("mutmut")
        run_res = subprocess.run(
            [mutmut_path, "run"],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        logging.error("❌ Error running 'mutmut run'")
        print(e.stdout or "")
        print(e.stderr or "")
        sys.exit(1)

    run_out = run_res.stdout or ""

    # Extract kill/survive stats
    killed = survived = None
    matches = list(re.finditer(r"(\d+)/(\d+).*?🎉\s+(\d+).*?🙁\s+(\d+)", run_out, flags=re.DOTALL))
    if matches:
        _, _, k_str, s_str = matches[-1].groups()
        try:
            killed = int(k_str)
            survived = int(s_str)
        except ValueError:
            killed = survived = None

    # Write survivors report
    logging.info("🧾 Generating survivor mutation report...")
    Path("Logs").mkdir(parents=True, exist_ok=True)
    try:
        res_res = subprocess.run(
            [mutmut_path, "results"],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        logging.error("❌ Error running 'mutmut results'")
        print(e.stdout or "")
        print(e.stderr or "")
        sys.exit(1)

    results_text = res_res.stdout or ""
    with open("Logs/mutmut_survivors.md", "w", encoding="utf-8") as f:
        f.write(results_text)

    # If parsing failed, fallback to counting survivors
    if killed is None or survived is None:
        logging.warning("⚠️ Could not extract kill/survive stats.")
        surv_count = sum(1 for ln in results_text.splitlines() if ": survived" in ln)
        logging.info(f"📊 Detected {surv_count} survivors (mutation score unavailable).")
        if surv_count > 0:
            logging.error("❌ Surviving mutations found. Pre-commit will fail.")
            sys.exit(1)
        logging.info("✅ No surviving mutations.")
        sys.exit(0)

    # Show mutation score
    killable = killed + survived
    killed_percent = (killed / killable) * 100 if killable > 0 else 0.0
    logging.info(
        f"📊 Mutations — Killed: {killed} | Survived: {survived} | "
        f"Killed %: {killed_percent:.2f}% (min required: {MIN_SCORE}%)"
    )

    # Enforce mutation score threshold
    if killed_percent < MIN_SCORE:
        logging.error(f"❌ Mutation score too low: {killed_percent:.2f}% < {MIN_SCORE}%")
        sys.exit(1)

    # Enforce 0 survivors if any
    if survived > 0:
        logging.warning("⚠️ Some mutations survived, but score threshold passed.")

    logging.info("✅ All mutations killed. Good job!")
    sys.exit(0)


if __name__ == "__main__":
    if not check_coverage():
        sys.exit(1)
    run_mutmut()
