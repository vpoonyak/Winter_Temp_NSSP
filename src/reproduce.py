"""One-command offline reproduction from committed provider-derived extracts."""
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
for script in ['build_temp_nssp_dataset.py', 'analyze.py', 'validate.py', 'build_report.py']:
    subprocess.run([sys.executable, str(root / 'src' / script)], cwd=root, check=True)
print('Final project reproduced successfully.')
