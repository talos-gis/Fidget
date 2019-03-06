import setuptools

import qtalos

setuptools.setup(
    name=qtalos.__name__,
    version=qtalos.__version__,
    author=qtalos.__author__,
    packages=['qtalos', 'qtalos.widgets', 'qtalos.backends'],
    extras_require={
        'PyQt': ['PyQt5'],
        'PySide': ['PySide']
    },
    python_requires='>=3.7.0',
    include_package_data=True,
    data_files=[
        ('', ['README.md', 'CHANGELOG.md']),
    ],
)
