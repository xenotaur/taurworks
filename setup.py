from setuptools import setup, find_packages

setup(
    name="taurworks",
    version="0.1",
    packages=find_packages(),
    install_requires=[],
    entry_points={
        "console_scripts": [
            "taurworks=taurworks.cli:main",
        ],
    },
)

