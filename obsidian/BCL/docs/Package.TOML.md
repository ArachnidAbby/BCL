# What is this?

The `package.toml` file descibes what libraries your program should use, where you main file is, and other compilation settings.

# Standard file.

```toml
# basic package info
[info]

name="myGame"
authors = ["Benjamin A."]
version = "0.1A"

# compiler settings
[compiler]

main = "src/main.bcl"
includePaths = ["includes"]

# external packages to be downloaded
[packages]

examplePkg = {link = "github.com/example/exampleForBCL", branch = "master"}
Example2 = {link = "github.com/example2/example2", version = "0.4"}
exampl3 = {link = "drive.google.com/ejkhsimvimei", direct = true}
```