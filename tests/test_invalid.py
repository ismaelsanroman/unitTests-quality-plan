#!/usr/bin/env python

"""
Windows-friendly mutation gate using `mutatest` (CLI) and `pytest`.
- Runs coverage first and enforces a minimum threshold.
- Then runs `mutatest` via its **console script** (not as a module) and parses results.
- Reads thresholds from env vars when provided: COVERAGE_MIN, MUTATION_MIN.
- Disables pytest plugin autoloading to avoid breakage from old third‑party plugins.

Comments are in English and there are no emojis by request.
"""

import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

DEFAULT_MIN = 80.0  # default threshold for coverage and mutation score

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def _get_thresholds() -> Tuple[float, float]:
    """Return (coverage_min, mutation_min) from env or defaults."""
    def _read(name: str, default: float) -> float:
        v = os.environ.get(name)
        if v is None:
            return default
        try:
            return float(v)
        except ValueError:
            logging.warning(f"[CONFIG] Invalid {name}={v!r}; using default {default}.")
            return default

    return _read("COVERAGE_MIN", DEFAULT_MIN), _read("MUTATION_MIN", DEFAULT_MIN)


def _which(cmd: str) -> str:
    """Find an executable on PATH or abort with a clear message."""
    path = shutil.which(cmd)
    if not path:
        logging.error(f"Executable '{cmd}' not found on PATH. Ensure it is installed in this environment.")
        sys.exit(1)
    return path


def run_pytest_coverage() -> Optional[float]:
    """Run pytest with coverage and return total coverage percentage if found."""
    logging.info("[COVERAGE] Running pytest with coverage...")

    # Isolate from third‑party plugins that may be incompatible.
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-p",
        "pytest_cov",  # load only pytest-cov explicitly
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=html",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        logging.error("[COVERAGE] Pytest coverage run failed.")
        print(e.stdout or e.stderr or str(e))
        return None

    stdout = result.stdout or ""

    for line in stdout.splitlines():
        if "TOTAL" in line and "%" in line:
            parts = line.strip().split()
            token = parts[-1]
            try:
                percent = float(token.replace("%", ""))
                logging.info(f"[COVERAGE] Detected total coverage: {percent:.2f}%")
                return percent
            except Exception:
                logging.warning(f"[COVERAGE] Could not parse percentage from line: {line}")
                continue

    logging.warning("[COVERAGE] Could not find coverage percentage in pytest output.")
    return None


def enforce_min_coverage(min_required: float) -> bool:
    percent = run_pytest_coverage()
    if percent is None:
        logging.error("[COVERAGE] Coverage not detected; failing the gate.")
        return False
    logging.info(f"[COVERAGE] Using threshold: {min_required:.2f}%")
    if percent >= min_required:
        logging.info("[COVERAGE] Coverage threshold met. Proceeding to mutation testing.")
        return True
    logging.error(f"[COVERAGE] Coverage too low: {percent:.2f}% (minimum {min_required}%).")
    return False


def run_mutatest() -> Tuple[str, int]:
    """Run mutatest via its console script and return (stdout+stderr, returncode)."""
    logging.info("[MUTATION] Running mutatest...")

    source_dir = os.environ.get("MUTATION_SOURCE", "src")

    # Keep pytest quiet and fail fast; also isolate plugins for the pytests that mutatest spawns.
    os.environ["PYTEST_ADDOPTS"] = "-q -x --disable-warnings"
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"

    mutatest_exe = _which("mutatest")  # use console script; do NOT run as module

    cmd = [mutatest_exe, "-s", source_dir]

    res = subprocess.run(cmd, capture_output=True, text=True)
    stdout = (res.stdout or "") + ("\n" + res.stderr if res.stderr else "")

    Path("Logs").mkdir(parents=True, exist_ok=True)
    (Path("Logs") / "mutatest_output.txt").write_text(stdout, encoding="utf-8")

    return stdout, res.returncode


def parse_mutatest_stats(output: str) -> Tuple[Optional[int], Optional[int]]:
    """Extract (killed, survived) from mutatest output when possible."""
    text = output

    m_k = re.search(r"(?mi)^\s*KILLED\s*[:=-]\s*(\d+)\b", text)
    m_s = re.search(r"(?mi)^\s*SURVIVED\s*[:=-]\s*(\d+)\b", text)
    if m_k and m_s:
        try:
            return int(m_k.group(1)), int(m_s.group(1))
        except Exception:
            pass

    m_k2 = re.search(r"(?i)killed\D+(\d+)", text)
    m_s2 = re.search(r"(?i)survived\D+(\d+)", text)
    if m_k2 and m_s2:
        try:
            return int(m_k2.group(1)), int(m_s2.group(1))
        except Exception:
            pass

    # Fallback: count tokens across lines
    killed_count = len(re.findall(r"(?mi)\bKILLED\b", text))
    survived_count = len(re.findall(r"(?mi)\bSURVIVED\b", text))
    if killed_count or survived_count:
        return killed_count, survived_count

    return None, None


def write_survivors_report(output: str) -> int:
    survivors_lines = [ln for ln in output.splitlines() if "SURVIVED" in ln]
    Path("Logs").mkdir(parents=True, exist_ok=True)
    (Path("Logs") / "mutatest_survivors.txt").write_text("\n".join(survivors_lines), encoding="utf-8")
    return len(survivors_lines)


def enforce_mutation_score(min_required: float) -> None:
    stdout, _ = run_mutatest()

    killed, survived = parse_mutatest_stats(stdout)
    survivors_detected = write_survivors_report(stdout)

    if killed is None or survived is None:
        logging.warning("[MUTATION] Could not parse exact killed/survived counts from mutatest output.")
        logging.info(f"[MUTATION] Detected {survivors_detected} survivor lines by fallback scan.")
        if survivors_detected > 0:
            logging.error("[MUTATION] Surviving mutations found. Failing the gate.")
            sys.exit(1)
        logging.info("[MUTATION] No survivors detected by fallback scan.")
        sys.exit(0)

    killable = killed + survived
    killed_percent = (killed / killable) * 100 if killable > 0 else 0.0

    logging.info(
        f"[MUTATION] Summary — Killed: {killed} | Survived: {survived} | "
        f"Killed %: {killed_percent:.2f}% (min required: {min_required}%)"
    )

    if killed_percent < min_required:
        logging.error(f"[MUTATION] Mutation score too low: {killed_percent:.2f}% < {min_required}%")
        sys.exit(1)

    if survived > 0:
        logging.warning("[MUTATION] Some mutations survived but score threshold was met. Consider tightening tests.")

    logging.info("[MUTATION] Threshold satisfied. Gate passed.")
    sys.exit(0)


if __name__ == "__main__":
    cov_min, mut_min = _get_thresholds()
    if not enforce_min_coverage(cov_min):
        sys.exit(1)
    enforce_mutation_score(mut_min)
