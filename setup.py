import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="torricelli",
    version="4.0.1",
    author="Francois C. Bocquet",
    author_email="f.posseik@fz-juelich.de",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fposseik/Torricelli",
    packages=["Torricelli"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='~=3.7',
    install_requires=['lmfit', 'pyqtgraph', 'h5py', 'numpy', 'scipy'],
    package_data={
        "" : ['*.py'],
        "Torricelli": ['*.py',
                       "imports/*.py", "imports/*.png",
                       "imports/Databases/*.txt", 'imports/Databases/*.csv', 'imports/Databases/*.ini',
                       'imports/Databases/DW/*.csv',
                       'imports/Databases/f1 and f2/*.nff',
                       'imports/Databases/Lattices/*.csv']}
)
