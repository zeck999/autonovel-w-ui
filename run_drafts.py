#!/usr/bin/env python3
"""Compatibility entry point: draft the selected novel through the orchestrator."""
import argparse
from run_pipeline import run_pipeline

if __name__ == "__main__":
    run_pipeline(argparse.Namespace(from_scratch=False, phase="drafting", max_cycles=None))
