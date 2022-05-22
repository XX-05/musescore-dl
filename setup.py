from setuptools import setup

setup(
    name="musescore-dl",
    version="0.1.0",
    install_requires=[
        "beautifulsoup4",
        "lxml",
        "requests",
        "svglib",
        "questionary",
        "click",
        "colorama"
    ],
    entry_points={
        "console_scripts": [
            "musescore-dl = musescore_dl:cli",
        ],
    },
)
