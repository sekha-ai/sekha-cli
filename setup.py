from setuptools import setup, find_packages

setup(
    name='sekha-cli',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'click>=8.0',
        'sekha-sdk>=1.0.0'
    ],
    entry_points={
        'console_scripts': [
            'sekha=sekha_cli.cli:cli',
        ],
    },
)
