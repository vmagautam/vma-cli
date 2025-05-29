from setuptools import setup, find_packages

setup(
    name="vma",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.0,<9.0",
        "jinja2",
        "PyYAML",
        "setuptools",
        "wheel",
        "twine",
        "requests",
        "urllib3",
        "chardet",
        # add any other dependencies you use
    ],
    entry_points={
        "console_scripts": [
            "vma=vma.cli:cli",
        ],
    },
)
