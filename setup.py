from setuptools import find_packages, setup

setup(
    name="taurworks",
    version="0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={"taurworks": ["resources/shell/taurworks-shell.sh"]},
    install_requires=[],
    extras_require={
        "dev": [
            "black",
            "ruff",
        ],
        "test": [],
    },
    entry_points={
        "console_scripts": [
            "taurworks=taurworks.cli:main",
        ],
    },
)
