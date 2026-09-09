#!/usr/bin/env python3
"""
Single-command runner to reproduce all headline evaluation results in <15 minutes.
Usage:
    python3 run_evaluation.py
"""

import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from evaluation.harness import run_full_benchmark

if __name__ == "__main__":
    print("=" * 80)
    print(" HIVER SDE INTERN TAKE-HOME ASSIGNMENT: EVALUATION REPRODUCTION HARNESS")
    print(" Target Brand: @AppleSupport | Dataset: 200 Hand-Labelled Golden Samples")
    print("=" * 80)
    run_full_benchmark()
