# Bens Compiled Language (BCL)

BCL (Ben's Compiled Language), is a compiled programming language that takes insperation from Java, C++, Rust, and Python.



# How it Works

The compiler is written in Python3.8 using llvm ir to compile.

# Project Setup
all projects must have a these files and directories
```
./project.json
./ExternalLibraries/
./src/Main.BCL
```

**./project.json**
```json
{
    "Project Name": "My First Project",
    "Authors": ["Benjamin Austin Jr"],
    "Main File": "src/Main.BCL",
    "External Packages":[],
    "Include Paths":[
        "ExternalLibraries/"
    ]
}
```

**./project.json (example2)**
```json
{
    "Project Name": "My First Project",
    "Authors": ["Benjamin Austin Jr"],
    "Main File": "src/Main.BCL",
    "External Packages":[
        {"name":"Twitter", "source":"github.com/twitter/twitterForBCL", "branch":"master"}
    ],
    "Include Paths":[
        "ExternalLibraries/"
    ]
}
```

# Package Setup
All packages must have these files
```python
#active director ./src/
./mypkg/packageInfo.json
./mypkg/src/Main.BCL
```

**packageInfo.json**
```json
{
    "Package Name": "testPackage",
    "Authors": ["Benjamin Austin Jr"],
    "Package Main": "src/Main.BCL"
}
```


## Visit `tests/Example` for more info