from setuptools import find_packages, setup

setup(
    name="taurworks",
    version="0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[],
    entry_points={
        "console_scripts": [
            "taurworks=taurworks.cli:main",
        ],
    },
)
