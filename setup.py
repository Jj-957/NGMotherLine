"""
Setup script para NGMotherLine
"""

from setuptools import setup, find_packages
from pathlib import Path

# Lê o README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text() if (this_directory / "README.md").exists() else ""

# Lê os requirements
requirements = []
if (this_directory / "requirements.txt").exists():
    requirements = (this_directory / "requirements.txt").read_text().splitlines()

setup(
    name="ngmotherline",
    version="0.1.0",
    author="NGMotherLine Team",
    author_email="team@ngmotherline.com",
    description="Engine de geração de legendas any-to-any com performance otimizada",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ngmotherline/ngmotherline",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Video",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
        "gpu": [
            "torch>=2.0.0+cu118",
            "torchaudio>=2.0.0+cu118",
        ],
    },
    entry_points={
        "console_scripts": [
            "motherline=cli.main:entry_point",
            "ngmotherline=cli.main:entry_point",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.txt", "*.md", "*.json"],
    },
    zip_safe=False,
    keywords="subtitle, transcription, translation, whisper, speech-to-text, any-to-any",
    project_urls={
        "Bug Reports": "https://github.com/ngmotherline/ngmotherline/issues",
        "Source": "https://github.com/ngmotherline/ngmotherline",
        "Documentation": "https://github.com/ngmotherline/ngmotherline/wiki",
    },
) 