import os
import subprocess
from io import StringIO
from pathlib import Path

resources_root = Path(os.path.realpath(__file__)).parent
qrc_path = resources_root / r'resources.qrc'
dst_path = resources_root.parent / r'src/fidget/backend/_resources.py'
rcc_path = r'c:\Python39\Scripts\pyside6-rcc.exe'
cmd = f'{rcc_path} {qrc_path}'

line_replace = {
    'from PySide6 import QtCore\n':
        'from fidget.backend.QtCore import QtCore\n',
    '# WARNING! All changes made in this file will be lost!\n':
        '# WARNING! All changes made in this file will be lost!\n'
        '# NOTE: this file was edited by Fidget to accommodate PySide6, PySide5 and PyQt5\n'
}

if __name__ == '__main__':
    result = subprocess.run(cmd, capture_output=True, encoding='utf-8')
    result.check_returncode()

    sink = StringIO(result.stdout)
    with open(dst_path, 'w') as dst:
        for line in sink:
            line = line_replace.get(line, line)
            dst.write(line)
