import setuptools

import qtalos

setuptools.setup(
    name=qtalos.__name__,
    version=qtalos.__version__,
    author=qtalos.__author__,
    packages=['qtalos', 'qtalos.widgets', ],
    install_requires=['PyQt5', ],
    python_requires='>=3.7.0',
    include_package_data=True,
    data_files=[
        ('', ['README.md', 'CHANGELOG.md']),
    ],
)
