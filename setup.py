from setuptools import setup

setup(
    name="musescore-dl",
    version="0.1.0",
    py_modules=["main"],
    install_requires=["beautifulsoup4", "lxml", "requests", "svglib"],
    entry_points={
        "console_scripts": [
            "musescore-dl = cli:cli",
        ],
    },
)
