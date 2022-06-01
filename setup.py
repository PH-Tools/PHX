import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="PHX",
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    author="PH-Tools",
    author_email="phtools@bldgtyp.com",
    description="Input / Output Passive House building energy model data.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PH-Tools/PHX",
    packages=setuptools.find_packages(exclude=["tests"]),
    include_package_data=True,
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "License :: OSI Approved :: GNU General Public License v3.0",
        "Operating System :: OS Independent"
    ],
    license="GPL-3.0"
)