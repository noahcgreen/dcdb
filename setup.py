from setuptools import setup


setup(
    name='dcdb',
    version='0.1',
    packages=['dcdb'],
    install_requires=['aenum', 'kivy', 'lupa', 'pyyaml'],
    tests_require=['pytest', 'pytest-datadir'],
)
