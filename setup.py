import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="Torricelli-fposseik", # Replace with your own username
    version="4.0rc0",
    author="Francois C. Bocquet",
    author_email="f.posseik@fz-juelich.de",
    description="A software to determine atomic spatial distribution from normal incidence x-ray standing wave data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fposseik/Torricelli",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='=3.7',
)
