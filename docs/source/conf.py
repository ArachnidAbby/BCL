# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

from pygments.lexer import RegexLexer
from pygments.token import (Comment, Keyword, Name, Number, Operator,
                            Punctuation, String, Whitespace)

sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

project = 'BCL'
copyright = '2022, Benjamin A.'
author = 'Benjamin A.'

# The full version, including alpha/beta/rc tags
release = '0.1.0'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = []

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
html_logo = "_static/experimental_BCL_LOGO.png"

html_sidebars = {
    '**': [
        'globaltoc.html',
    ]
}


class BCLLexer(RegexLexer):
    name = 'bcl'
    aliases = ['bcl']
    filenames = ['*.bcl']
    tokens = {
        'root': [
            (r'[\s\n]+', Whitespace),
            (r'(["\'])(?:(?=(\\?))\2.)*?\1', String.Double),
            (r'\d+', Number),
            (r'(if)|(elif)|(else)|(define)|(struct)|(for)|(import)|(yield)|(return)',
             Keyword.Reserved),
            (r'(i8)|(i16)|(i32)|(i64)|(f64)|(f128)|(bool)|' +
             r'(char)|(str)|(strlit)', Keyword.Type),
            (r'\s+(or)|(and)|(not)|(in)\s+', Operator.Word),
            (r'[\=\+\-\*\\\%\%\<\>]', Operator),
            (r'[\{\};\(\)\:\[\]\,]', Punctuation),
            (r'[a-zA-Z0-9_]+(?=\(.*\))', Name.Function),
            (r'//.*$', Comment.Single),
            (r'\w[\w\d]*', Name.Other)
        ]
    }


def setup(app) -> None:
    from sphinx.highlighting import lexers
    lexers['bcl'] = BCLLexer()
