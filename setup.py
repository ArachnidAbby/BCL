from setuptools import find_packages, setup

with open("readme.md", "r", encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().split("\n")
    requirements = [x.replace("git+","llvmlite @ git+") for x in requirements if x.startswith("#") and x!='']
    print(requirements)

setup(
    name='Bens Compiled Language',
    version='0.6.1',
    author='Benjamin Austin Jr',
    author_email='N/A',
    license='Unspecified',
    description='The CLI tool for BCL development',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='github.com/spidertyler2005/BCL',
    package_dir={"": "src"},
    package_data={"": ["*.bcl"]},
    py_modules=["main", "bcl", "compile", "errors", "linker", "lexer", "parser",
                "parserbase", "Ast"],
    packages=find_packages(where="src"),  # find_packages(),
    install_requires=[requirements],
    python_requires='>=3.11',
    classifiers=[
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    entry_points='''
        [console_scripts]
        bcl=bcl:main
    '''
)
