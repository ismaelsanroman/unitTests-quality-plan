#!/usr/bin/env python
# scripts/mutmut_check.py

import logging
import re
import shutil
import subprocess
import sys
from pathlib import Path

MIN_SCORE = 80  # Minimum threshold for coverage and % killed

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def get_executable_path(cmd: str) -> str:
    """Finds the absolute path to an executable."""
    exe_path = shutil.which(cmd)
    if not exe_path:
        logging.error(f"Could not find '{cmd}' executable in PATH.")
        sys.exit(1)
    return exe_path


def check_coverage() -> bool:
    logging.info("🚦 [MUTATION CHECK] Checking minimum coverage before mutations...")
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
        logging.error("❌ [MUTATION CHECK] Error running coverage")
        # Sometimes coverage is printed in stdout
        print(e.stdout or e.stderr or str(e))
        return False

    stdout = result.stdout or ""
    for line in stdout.splitlines():
        if "TOTAL" in line and "%" in line:
            try:
                percent = float(line.strip().split()[-1].replace("%", ""))
            except Exception as ex:
                logging.warning(f"Failed to parse coverage percent: {ex} | line: {line}")
                continue
            if percent >= MIN_SCORE:
                logging.info("✅ [MUTATION CHECK] Coverage OK. Proceeding to mutmut!")
                return True
            logging.error(
                f"❌ [MUTATION CHECK] Insufficient coverage: {percent:.2f}% (minimum {MIN_SCORE}%)"
            )
            return False

    logging.warning("⚠️ [MUTATION CHECK] Could not extract coverage percent from pytest output.")
    return False


def run_mutmut():
    logging.info("🧬 Running mutation tests on the source code...")

    # Avoid pytest plugins interference
    sys.environ = getattr(sys, "environ", os.environ)
    sys.environ["PYTEST_ADDOPTS"] = "-q -x --disable-warnings"

    # 1) Run mutmut and CAPTURE stdout to parse counters
    try:
        mutmut_run_path = get_executable_path("mutmut")
        run_res = subprocess.run(
            [mutmut_run_path, "run"],
            capture_output=True,
            text=True,
            check=True,  # mutmut returns 0 even if there are survivors
        )
    except subprocess.CalledProcessError as e:
        logging.error("❌ Error running: mutmut run")
        print(e.stdout or "")
        print(e.stderr or "")
        sys.exit(1)

    run_out = run_res.stdout or ""
    # 2) Get killed and survived from the final “ticker”: … 🎉 <killed> … 🙁 <survived> …
    killed = survived = None
    matches = list(re.finditer(r"(\d+)/(\d+).*?🎉\s+(\d+).*?🙁\s+(\d+)", run_out, flags=re.DOTALL))
    if matches:
        _, _, k_str, s_str = matches[-1].groups()
        try:
            killed = int(k_str)
            survived = int(s_str)
        except ValueError:
            killed = survived = None

    # 3) Save the list of survivors in Markdown
    logging.info("🧾 Generating mutation survivors report...")
    Path("Logs").mkdir(parents=True, exist_ok=True)
    mutmut_results_path = get_executable_path("mutmut")
    res_res = subprocess.run([mutmut_results_path, "results"], capture_output=True, text=True)
    results_text = res_res.stdout or ""
    with open("Logs/mutmut_survivors.md", "w", encoding="utf-8") as f:
        f.write(results_text)

    # 4) If counters couldn't be extracted, at least show survivors
    if killed is None or survived is None:
        logging.warning("⚠️ Could not extract 'mutmut run' summary.")
        surv_count = sum(1 for ln in results_text.splitlines() if ": survived" in ln)
        logging.info(f"📊 Survivors detected: {surv_count} (cannot calculate % killed).")
        if surv_count > 0:
            logging.error("❌ Surviving mutations detected. Pre-commit must fail.")
            sys.exit(1)
        logging.info("✅ No survivors detected.")
        sys.exit(0)

    # 5) Calculate and show % killed (only with killables: killed + survived)
    killable = killed + survived
    killed_percent = (killed / killable) * 100 if killable > 0 else 0.0
    logging.info(
        f"📊 Mutations — Killed: {killed} | Survived: {survived} | "
        f"% killed: {killed_percent:.2f}% (min {MIN_SCORE}%)"
    )

    # 6) Decide the hook result
    if killed_percent < MIN_SCORE:
        logging.error(
            f"❌ Ratio of killed mutations ({killed_percent:.2f}%) is less than minimum ({MIN_SCORE}%)."
        )
        sys.exit(1)

    # Extra: if % passes but survivors remain, fail anyway (optional)
    if survived > 0:
        logging.error("❌ Mutations survived. Improve your tests.")
        sys.exit(1)

    logging.info("✅ All mutations were killed. Great job!")
    sys.exit(0)


if __name__ == "__main__":
    if not check_coverage():
        sys.exit(1)
    run_mutmut()
