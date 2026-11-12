"""Coordinator-only CLI wrapper for a frozen-config holdout adapter.

This module never chooses or opens a data folder itself. The coordinator must
provide the frozen config, an explicit holdout path and a runner adapter.
"""
import argparse
import importlib
import json
try:
    from .phase3 import run_holdout
except ImportError:  # direct script execution
    from phase3 import run_holdout


def _load_callable(spec):
    module_name,sep,function_name=spec.partition(':')
    if not sep: raise ValueError('--runner must be written as package.module:function')
    fn=getattr(importlib.import_module(module_name),function_name)
    if not callable(fn): raise TypeError(f'{spec} is not callable')
    return fn


def main():
    parser=argparse.ArgumentParser(description='Coordinator-only frozen Phase 3 holdout runner')
    parser.add_argument('--config',required=True,help='frozen JSON config with approach, prereg_dir, frozen_date and sha256')
    parser.add_argument('--prices',required=True,help='explicit holdout price directory; development paths are refused')
    parser.add_argument('--runner',required=True,help='adapter as package.module:function(cfg, price_folder)')
    parser.add_argument('--coordinator-only',action='store_true',required=True,help='required explicit coordinator gate')
    args=parser.parse_args()
    result=run_holdout(args.config,args.prices,_load_callable(args.runner),caller_role='coordinator')
    print(json.dumps(result,default=str,indent=2))


if __name__=='__main__': main()
