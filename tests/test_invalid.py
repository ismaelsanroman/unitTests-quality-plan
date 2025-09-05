#!/usr/bin/env python

"""
Mutation test gate for Windows using `mutatest` and `pytest`.
- Runs coverage first (via pytest + coverage) and enforces a minimum threshold.
- Then runs `mutatest` and parses results to compute a mutation score.
- Fails the process (exit code 1) if the mutation score is below MIN_SCORE or if there are survivors
  when score parsing is unavailable but survivors are detected in the textual output.

Notes for Windows compatibility:
- Executables are invoked as Python modules using `sys.executable -m <module>` to avoid PATH issues.
- All file writes go under a local `Logs/` folder.
- Output parsing is resilient to small format changes; if exact numbers cannot be parsed, it falls back
  to detecting "SURVIVED" lines and failing accordingly.

Comments are in English and there are no emojis by request.
"""

import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

# Threshold used both for coverage minimum and mutation score minimum (%).
MIN_SCORE = 80

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def run_pytest_coverage() -> Optional[float]:
    """Run pytest with coverage and return the total coverage percentage if found.

    Returns
    -------
    Optional[float]
        The coverage percentage (0-100) if parsed successfully, otherwise None.
    """
    logging.info("[COVERAGE] Running pytest with coverage...")

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=html",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        logging.error("[COVERAGE] Pytest coverage run failed.")
        # Show captured output to help debugging in CI.
        print(e.stdout or e.stderr or str(e))
        return None

    stdout = result.stdout or ""

    # Typical coverage terminal output contains a line with TOTAL ... XX%
    # We scan for a percentage at the end of the TOTAL line.
    for line in stdout.splitlines():
        if "TOTAL" in line and "%" in line:
            parts = line.strip().split()
            # The last token normally looks like '85%' or '85.00%'
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
    """Run coverage and enforce the minimum threshold.

    Returns True if coverage is OK, False otherwise.
    """
    percent = run_pytest_coverage()
    if percent is None:
        logging.error("[COVERAGE] Coverage not detected; failing the gate.")
        return False

    if percent >= min_required:
        logging.info("[COVERAGE] Coverage threshold met. Proceeding to mutation testing.")
        return True

    logging.error(
        f"[COVERAGE] Coverage too low: {percent:.2f}% (minimum {min_required}%)."
    )
    return False


def run_mutatest() -> Tuple[str, int]:
    """Run mutatest and return its stdout plus return code.

    Returns
    -------
    Tuple[str, int]
        The captured stdout and the process return code.
    """
    logging.info("[MUTATION] Running mutatest...")

    # Many projects expose tests via pytest by default, so we rely on pytest discovery.
    # `-s src` narrows the mutation targets to the source folder.
    # If your code lives somewhere else, adjust the -s argument.

    # Optionally allow override via environment variables in CI if needed.
    source_dir = os.environ.get("MUTATION_SOURCE", "src")

    # Keep pytest quiet and fail fast to save cycles.
    os.environ["PYTEST_ADDOPTS"] = "-q -x --disable-warnings"

    cmd = [
        sys.executable,
        "-m",
        "mutatest",
        "-s",
        source_dir,
    ]

    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,  # mutatest can return non-zero; we still want its output.
        )
    except FileNotFoundError:
        logging.error(
            "[MUTATION] mutatest is not installed or not importable. Install with `pip install mutatest`."
        )
        sys.exit(1)

    stdout = (res.stdout or "") + ("\n" + res.stderr if res.stderr else "")

    # Persist full stdout/stderr for later inspection.
    Path("Logs").mkdir(parents=True, exist_ok=True)
    (Path("Logs") / "mutatest_output.txt").write_text(stdout, encoding="utf-8")

    return stdout, res.returncode


def parse_mutatest_stats(output: str) -> Tuple[Optional[int], Optional[int]]:
    """Attempt to extract killed and survived counts from mutatest output.

    The function tries a couple of patterns to be robust across mutatest versions.

    Returns
    -------
    (killed, survived) as integers, or (None, None) if parsing failed.
    """
    text = output

    # Common summary snippets may include lines like:
    #   "KILLED: 12"
    #   "SURVIVED: 3"
    # or lines with categories and counts separated by colons or hyphens.
    killed = None
    survived = None

    # Pattern 1: Standalone KILLED/SURVIVED key-value pairs
    m_k = re.search(r"(?mi)^\s*KILLED\s*[:=-]\s*(\d+)\b", text)
    m_s = re.search(r"(?mi)^\s*SURVIVED\s*[:=-]\s*(\d+)\b", text)
    if m_k and m_s:
        try:
            killed = int(m_k.group(1))
            survived = int(m_s.group(1))
            return killed, survived
        except Exception:
            pass

    # Pattern 2: Count tokens anywhere (less strict), first match wins
    m_k2 = re.search(r"(?i)killed\D+(\d+)", text)
    m_s2 = re.search(r"(?i)survived\D+(\d+)", text)
    if m_k2 and m_s2:
        try:
            killed = int(m_k2.group(1))
            survived = int(m_s2.group(1))
            return killed, survived
        except Exception:
            pass

    # Pattern 3: Fallback by counting label occurrences per test result lines
    # Many per-case lines contain the words KILLED or SURVIVED. We count them.
    survived_count = len(re.findall(r"(?mi)\bSURVIVED\b", text))
    killed_count = len(re.findall(r"(?mi)\bKILLED\b", text))

    # If at least one of these is non-zero, assume these counts are usable.
    if survived_count or killed_count:
        return killed_count, survived_count

    return None, None


def write_survivors_report(output: str) -> int:
    """Write a survivors-only report file and return the number of survivors detected.

    This filters lines that contain the word SURVIVED to create a concise report.
    """
    survivors_lines = [ln for ln in output.splitlines() if "SURVIVED" in ln]
    Path("Logs").mkdir(parents=True, exist_ok=True)
    (Path("Logs") / "mutatest_survivors.txt").write_text(
        "\n".join(survivors_lines), encoding="utf-8"
    )
    return len(survivors_lines)


def enforce_mutation_score(min_required: float) -> None:
    """Run mutatest, compute score, and enforce thresholds.

    Exits the process with code 0 on success or 1 on failure.
    """
    stdout, _ = run_mutatest()

    killed, survived = parse_mutatest_stats(stdout)

    # Always emit a survivors report to aid triage.
    survivors_detected = write_survivors_report(stdout)

    if killed is None or survived is None:
        logging.warning(
            "[MUTATION] Could not parse exact killed/survived counts from mutatest output."
        )
        logging.info(
            f"[MUTATION] Detected {survivors_detected} survivor lines by fallback scan."
        )
        if survivors_detected > 0:
            logging.error("[MUTATION] Surviving mutations found. Failing the gate.")
            sys.exit(1)
        logging.info("[MUTATION] No survivors detected by fallback scan.")
        sys.exit(0)

    # Compute mutation score (killed / (killed + survived) * 100)
    killable = killed + survived
    killed_percent = (killed / killable) * 100 if killable > 0 else 0.0

    logging.info(
        f"[MUTATION] Summary — Killed: {killed} | Survived: {survived} | "
        f"Killed %: {killed_percent:.2f}% (min required: {min_required}%)"
    )

    if killed_percent < min_required:
        logging.error(
            f"[MUTATION] Mutation score too low: {killed_percent:.2f}% < {min_required}%"
        )
        sys.exit(1)

    if survived > 0:
        logging.warning(
            "[MUTATION] Some mutations survived but score threshold was met. Consider tightening tests."
        )

    logging.info("[MUTATION] Threshold satisfied. Gate passed.")
    sys.exit(0)


if __name__ == "__main__":
    if not enforce_min_coverage(MIN_SCORE):
        sys.exit(1)
    enforce_mutation_score(MIN_SCORE)
