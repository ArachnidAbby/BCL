# Setting up your workspace

The recommended workspace is VS Code and you should install all of the [recommended extensions](./.vscode/extensions.json).
Git must be installed and configured with a name appropriate and indentifiable (Make it the same as or VERY similar to your github).

## Changing the [settings.json](./.vscode/settings.json)

Try not to change this for personal preference exclusively. If you decide that a change should be made here, then put it in it's own commit.
By doing this, we can reject settings changes (when needed) without rejecting all of your code.

## Pull Requests

Try your best not to make large Pull requests. Adding too many features at once could get your entire pull request denied despite it adding possibly good features. Getting a large pull request denied because of 1 major issue would not be fun.

# Update the Readme and docs

If needed, update the readme and docs with the most accurate information.

---

# Code Formatting (Typing)

Code is checked using Mypy. I have found it to be the nicest to work with, but this could change in the future.
Try to keep up with any updates to the static type checker being used.

### Avoid excessive uses of `# type: ignore`!
*do I need to explain this?*

## Avoid using strings as type annotations

This can sometimes be unavoidable, but try your best to use it sparingly or for organizational purposes only (Ex: a class is defined much further down, but a type annotation needs to be used). This is also useful if you are having circular imports.

---

# Code formatting (PEP8 -- modified)

This repo very loosely follows pep8 formatting. Do not worry about the 80 char limit, but do ensure that lines are most readable.

**Just use Flake8**

## avoid one-liners

Unless it is for very simple logic avoid these:
```python

def foo(y):
    # this is painful. All instances of this currently in production will be slowly removed
    x = 69 if y.lower() == "bar" else 420 
    return x

# This sucks to read 82% of the time. 
my_list = #[My long list comprehension I am too lazy to write]
```


## Always use `__slots__` unless you need a dict

Its a performance boost, use it or your PR will not be considered. It takes very little time.

reasons to use it:
- Memory usage reduction (Python has high usage to begin with, we gotta try to keep this low)
- Speedup in instantiation times (No need to create a dict!)

## No Licenses in code (unless necessary)

You may not under any circumstance place an additional license in your submitted code UNLESS you are including it from another project with a seperate license.

You also may never modify the LICENSE file unless given explicit permission.

## include detailed comments for confusing code

**this is a no-brainer**

If you can, avoid confusing code.

## Include doc comments for other developers

Doc comments are exclusively for other developers unless a compiler-plugin-api is made.

## Write and run tests!

Your PR will be denied if it does not pass tests. Also, include failing and passing tests for correct and common error behavior.
Also note, some bugs cause tests to not work when run together, but work when run seperately.

<br>...

*and lastly*

# Use common sense!