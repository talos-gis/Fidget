import setuptools

import fidget

setuptools.setup(
    name=fidget.__name__,
    version=fidget.__version__,
    author=fidget.__author__,
    description='Fidget is an adapter of Qt into a functional-style interface. Fidget can be used seamlessly with PyQt5'
                ' and PySide2. Fidget is designed to create an effortless and rich UI for data science and analysis.'
                f' See [the github page]({fidget.__url__}) for more details',
    url=fidget.__url__,
    packages=['fidget', 'fidget.core', 'fidget.widgets', 'fidget.backend'],
    extras_require={
        'PyQt': ['PyQt5'],
        'PySide': ['PySide2']
    },
    python_requires='>=3.7.0',
    include_package_data=True,
    data_files=[
        ('', ['README.md', 'CHANGELOG.md']),
    ],
)
