"""
============================================================================
  RUN_ALL.PY  --  Run every regression test
============================================================================

    python tests/run_all.py            all tests
    python tests/run_all.py mastery    only tests whose name contains "mastery"
    python tests/run_all.py -v         also print each test's output

Each tests/test_*.py is a plain script run in its own process (headless, with
a throw-away save folder - your real saves are never touched); it passes if
it exits cleanly. Needs the same packages as the game (pygame-ce, numpy).
Takes a few minutes: several tests play whole AI matches.
============================================================================
"""

import glob
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TIMEOUT = 900


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    verbose = "-v" in sys.argv[1:]
    tests = sorted(glob.glob(os.path.join(HERE, "test_*.py")))
    if args:
        tests = [t for t in tests if any(a in os.path.basename(t) for a in args)]
    failed = []
    t_all = time.time()
    for t in tests:
        name = os.path.basename(t)[:-3]
        t0 = time.time()
        try:
            p = subprocess.run([sys.executable, t], cwd=os.path.dirname(HERE),
                               capture_output=True, text=True, timeout=TIMEOUT)
            ok, out = p.returncode == 0, p.stdout + p.stderr
        except subprocess.TimeoutExpired:
            ok, out = False, "timed out after %ds" % TIMEOUT
        print("%-4s %-28s %5.1fs" % ("ok" if ok else "FAIL", name, time.time() - t0),
              flush=True)
        if verbose or not ok:
            print("\n".join("     | " + ln for ln in out.strip().splitlines()[-40:]))
        if not ok:
            failed.append(name)
    print("\n%d / %d passed in %.0fs%s" % (len(tests) - len(failed), len(tests),
                                         time.time() - t_all,
                                         ("  - FAILED: " + ", ".join(failed)) if failed else ""))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
