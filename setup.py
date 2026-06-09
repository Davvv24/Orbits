import setuptools

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()


REQUIREMENTS = [
    "matplotlib", 
    "numpy"
    ]


CLASSIFIERS = [
    # see https://pypi.org/classifiers/
    "Intended Audience :: Science/Research",
    "Programming Language :: Python :: 3",
    "Operating System :: OS Independent",
    ]

setuptools.setup(
    name="orbits",
    version="1.0.0",
    author="Davide Rizzo",
    description="A solar system simulation..",
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    classifiers=CLASSIFIERS,
    python_requires=">=3.10",
    install_requires=REQUIREMENTS
)