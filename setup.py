import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hsp",
    version="1.0.3",
    author="Julian Flesch",
    author_email="julianflesch@gmail.com",
    keywords="hochschulsport uni Tübingen",
    description="hochschulsport course booking",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JulianFlesch/hsp",
    project_urls={
        "Documentation": "https://github.com/JulianFlesch/hsp",
        "Source": "https://github.com/JulianFlesch/hsp"
        },
    packages=["hsp"],
    install_requires=[
        "pyyaml",
        "selenium",
        "Gecko"
        ],
    scripts=[
        "bin/hsp"],
    classifiers=[
        "Topics :: Scraping ::  Hochschulsport Tübingen",
    ],
)
