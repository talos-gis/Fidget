from setuptools import setup, find_packages

from src.fidget import (
    __package_name__,
    __author__,
    __author_email__,
    __maintainer__,
    __maintainer_email__,
    __license__,
    __url__,
    __version__,
    __description__,
)

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 3',
]

__readme__ = open('README.md', encoding="utf-8").read()
__readme_type__ = 'text/markdown'

package_root = 'src'   # package sources are under this dir
packages = find_packages(package_root)  # include all packages under package_root
package_dir = {'': package_root}  # packages sources are under package_root

setup(
    name=__package_name__,
    version=__version__,
    author=__author__,
    author_email=__author_email__,
    maintainer=__maintainer__,
    maintainer_email=__maintainer_email__,
    license=__license__,
    url=__url__,
    long_description=__readme__,
    long_description_content_type=__readme_type__,
    description=__description__,
    classifiers=classifiers,
    packages=packages,
    package_dir=package_dir,
    extras_require={
        'qt': ['PySide6'],
        'PySide': ['PySide6'],
        'PySide6': ['PySide6'],
        'PySide2': ['PySide2'],
        'PyQt': ['PyQt5'],
        # 'PyQt6': ['PyQt6'],
        'PyQt5': ['PyQt5'],
    },
    python_requires='>=3.7.0',
)
