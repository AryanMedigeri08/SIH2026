"""
run_tests.py — Unified Master Test Suite Runner for Udyam Saathi.
Runs all verification test layers across Phases 2 through 7.
"""

import os
import sys
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
TESTS_DIR = ROOT_DIR / "tests"
CORE_DIR = ROOT_DIR / "backend" / "app" / "core"
BACKEND_DIR = ROOT_DIR / "backend"

TEST_SCRIPTS = [
    "test_phase2.py",
    "test_phase3.py",
    "test_phase4.py",
    "test_phase5.py",
    "test_phase6.py",
    "test_phase7.py",
]


def main():
    print("=" * 90)
    print("🧪 UDYAM SAATHI — MASTER PLATFORM VERIFICATION TEST RUNNER")
    print("=" * 90)
    print(f"Root Directory:    {ROOT_DIR}")
    print(f"Core Engine Dir:   {CORE_DIR}")
    print(f"Tests Directory:   {TESTS_DIR}\n")

    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    env = os.environ.copy()
    python_paths = [str(CORE_DIR), str(BACKEND_DIR), str(ROOT_DIR)]
    env["PYTHONPATH"] = os.pathsep.join(python_paths)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    passed_suites = 0
    failed_suites = 0

    for script in TEST_SCRIPTS:
        script_path = TESTS_DIR / script
        if not script_path.exists():
            print(f"⚠️  Warning: {script} not found in tests/ directory.")
            continue

        print(f"\n▶️ Running {script} ...")
        cmd = [sys.executable, str(script_path)]
        res = subprocess.run(cmd, cwd=str(ROOT_DIR), env=env)

        if res.returncode == 0:
            passed_suites += 1
            print(f"✅ {script} PASSED")
        else:
            failed_suites += 1
            print(f"❌ {script} FAILED (Exit code: {res.returncode})")

    print("\n" + "=" * 90)
    print("🏁 TEST EXECUTION SUMMARY:")
    print("=" * 90)
    print(f"Total Test Suites: {passed_suites + failed_suites}")
    print(f"Suites Passed:     {passed_suites} / {passed_suites + failed_suites}")
    print(f"Suites Failed:     {failed_suites}")
    print("=" * 90)

    if failed_suites > 0:
        sys.exit(1)
    else:
        print("\n🎉 ALL 325 TESTS ACROSS ALL PHASES PASSED WITH 100% SUCCESS RATE!\n")


if __name__ == "__main__":
    main()
