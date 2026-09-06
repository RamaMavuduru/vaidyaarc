"""
Validation Runner for Phase 12.5: VaidyaArc Brain Acceptance & Integration Readiness.

Executes and validates:
- 10 End-to-End Synthetic Patient Journeys
- Multi-Turn State Integrity
- Adversarial Safety Attack Invariants
- Missing-Information Integrity (Missing != Absent)
- Full Provenance Traceability
- Cross-Phase Compatibility
- Malformed-Input Robustness
- Deterministic Repeatability
- Latency & Baseline Timing Benchmarks

ZERO-LLM. 100% DETERMINISTIC.
"""

import sys
import os
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from tests._phase12_5_brain_acceptance_tests import run_all_tests


def main():
    print("=" * 80)
    print("VAIDYAARC PHASE 12.5 BRAIN ACCEPTANCE VALIDATION RUNNER")
    print("=" * 80)
    start_total = time.time()
    try:
        run_all_tests()
        total_time = time.time() - start_total
        print(f"\n[BENCHMARK] Total Phase 12.5 Acceptance Suite Execution Time: {total_time:.2f}s")
        print("=" * 80)
        sys.exit(0)
    except Exception as e:
        print(f"\n[FATAL] Phase 12.5 Validation encountered unhandled error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
