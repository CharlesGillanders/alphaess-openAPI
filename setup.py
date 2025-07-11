from setuptools import setup, find_packages

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="alphaessopenapi",
    version="0.0.15",
    author="Charles Gillanders",
    author_email="charles@charlesgillanders.com",
    description="A python library to retrieve energy statistics from your Alpha ESS inverter by polling the Official Alpha ESS Open API.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CharlesGillanders/alphaess-openAPI",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)
