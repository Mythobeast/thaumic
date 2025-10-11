import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="thaumic",
    version="1.3.7",
    author_email="robert.rapplean@dhha.org",
    description="Database access tools that focus on dynamically adjusting the schema",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://dev.azure.com/DHHA/DHHA/_git/PythonScripts",
    packages=['thaumic',
              'thaumic.base',
              'thaumic.typemappings',
              'thaumic.adapters',
              'thaumic.mariadb',
              'thaumic.mocksql',
        ],
    # This allows me to put thaumic.x in subdirectory ./x instead of in thaumic/x
    package_dir={'thaumic': ''},
    # setuptools.find_packages(exclude=['tests', 'checkers', 'visitpath', 'nagiosanalysis',
    #                                            'tests.*', 'checkers.*', 'visitpath.*', 'nagiosanalysis.*',
    #                                            'tests.*.*', 'checkers.*.*', 'visitpath.*.*', 'nagiosanalysis.*.*']),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    setup_requires=["wheel"],
    python_requires='>=3.9',
    install_requires=[
        'mysqlclient>=2.0.3',
        'mariadb-connector>=2.2.9',
        'PyMySQL==0.9.3',
        'pyodbc==4.0.34',
    ]
)
