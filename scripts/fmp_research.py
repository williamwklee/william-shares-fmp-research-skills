"""Repository CLI; installable skill packages bundle the same versioned modules."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from fmp_skills.common import *
from fmp_skills.institutional import *
from fmp_skills.funds import *
from fmp_skills.earnings import *
from fmp_skills.company import *
from fmp_skills.api import fetch
from fmp_skills.cli import main
if __name__=='__main__':main()
