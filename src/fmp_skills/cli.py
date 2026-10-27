"""Repository command aliases for the same validated standalone runner."""
import argparse,sys
from pathlib import Path
from .entry import run
from .institutional import institutional,holders
from .funds import funds
from .earnings import earnings
from .company import company
REPORTS={"institutional":institutional,"holders":holders,"earnings":earnings,"funds":funds,"company":company}

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest="command",required=True)
    for name in REPORTS:
        q=sub.add_parser(name);q.add_argument("--input",type=Path,required=True);q.add_argument("--output",type=Path,required=True)
    q=sub.add_parser("fetch");q.add_argument("--endpoint",required=True);q.add_argument("--params",default="{}");q.add_argument("--output",type=Path,required=True)
    a=p.parse_args();original=sys.argv
    args=[original[0],"--output",str(a.output)]
    if a.command=="fetch":args += ["--fetch",a.endpoint,"--params",a.params]
    else:args += ["--input",str(a.input)]
    try:
        sys.argv=args
        run(REPORTS.get(a.command))
    finally:sys.argv=original
