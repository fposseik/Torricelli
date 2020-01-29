import setuptools

# see: https://docs.python.org/3/distutils/setupscript.html
# see: https://setuptools.readthedocs.io/en/latest/setuptools.html

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="torricelli-fposseikk", # Replace with your own username
    version="3.0rc0",
    author="Francois C. Bocquet",
    author_email="f.posseik@fz-juelich.de",
    maintainer="Francois C. Bocquet",
    maintainer_email="f.posseik@fz-juelich.de",
    description="A software to determine atomic spatial distribution from normal incidence x-ray standing wave data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fposseik/Torricelli",
    python_requires='~=3.7', #avoid 3.8, but stays flexible with 3.7.n    
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
    ],

    install_requires=["lmfit>=1.0", 'h5py>=2.9', 'pyqtgraph>=0.10'],
    
    #packages=setuptools.find_packages('torricelli'),
    packages=['torricelli'],
    #package_dir={"torricelli": "torricelli"},
    #py_modules=['torricelli'],
    #include_package_data=True, # this requires a MANIFEST.in --> pain in the neck!
    package_data={
        "torricelli": ['*.py',
                       "imports/*.py", "imports/*.png",
                       "imports/Databases/*.txt", 'imports/Databases/*.csv', 'imports/Databases/*.ini',
                       'imports/Databases/DW/*.csv',
                       'imports/Databases/f1 and f2/*.nff',
                       'imports/Databases/Lattices/*.csv'] }
)
