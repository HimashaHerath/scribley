from setuptools import setup, find_packages

setup(
    name="scribley",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "python-dotenv",
        "requests",
        "pyyaml",
        "schedule",
        "click",
        "markdown",
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "pydantic"
    ],
    entry_points={
        'console_scripts': [
            'scribley=scribley.cli:main',
        ],
    },
    author="Himasha",
    description="Medium article publishing automation tool",
    keywords="medium, automation, publishing",
    python_requires=">=3.9",
) 