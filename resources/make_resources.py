import subprocess
from io import StringIO

qrc_path = r'resources/resources.qrc'
dst_path = r'fidget/backend/_resources.py'

cmd = f'pyside2-rcc.exe -py3 "{qrc_path}"'

line_replace = {
    'from PySide2 import QtCore\n':
        'from fidget.backend.QtCore import QtCore\n',
    '# WARNING! All changes made in this file will be lost!\n':
        '# WARNING! All changes made in this file will be lost!\n'
        '# NOTE: this file was edited by Fidget to accommodate both PySide2 and PyQt5\n'
}

if __name__ == '__main__':
    result = subprocess.run(cmd, capture_output=True, encoding='utf-8')
    result.check_returncode()

    sink = StringIO(result.stdout)
    with open(dst_path, 'w') as dst:
        for line in sink:
            line = line_replace.get(line, line)
            dst.write(line)
