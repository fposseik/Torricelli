import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="torricelli-fposseikk", # Replace with your own username
    version="4.0.1",
    author="Example Author",
    author_email="f.posseik@fz-juelich.de",
    maintainer="Francois C. Bocquet",
    maintainer_email="f.posseik@fz-juelich.de",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fposseik/Torricelli",
    packages=["torricelli"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    package_data={
        "torricelli": ['*.py',
                       "imports/*.py", "imports/*.png",
                       "imports/Databases/*.txt", 'imports/Databases/*.csv', 'imports/Databases/*.ini',
                       'imports/Databases/DW/*.csv',
                       'imports/Databases/f1 and f2/*.nff',
                       'imports/Databases/Lattices/*.csv']}
)