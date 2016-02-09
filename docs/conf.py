# -*- coding: utf-8 -*-
#
# lighthouse documentation build configuration file, created by
# sphinx-quickstart on Wed Apr  1 19:21:44 2015.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

import sys
import os

sys.path.insert(0, os.path.abspath('..'))

import sphinx_bootstrap_theme
import lighthouse

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

# -- General configuration ------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.coverage',
    'sphinx.ext.viewcode',
    'sphinx.ext.extlinks',
]
if not on_rtd:
    extensions.append("sphinxcontrib.spelling")

templates_path = ['templates']

source_suffix = '.rst'

master_doc = 'index'

project = u'lighthouse'
copyright = u'2015, William Glass'
author = u'William Glass'

version = release = lighthouse.__version__

language = None


autodoc_member_order = "bysource"
autoclass_content = "both"
autodoc_docstring_signature = False

coverage_skip_undoc_in_source = True
coverage_ignore_modules = [
    "lighthouse.scripts.writer",
    "lighthouse.scripts.reporter",
]

spelling_word_list_filename = "spelling_wordlist.txt"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = []

# The reST default role (used for this markup: `text`) to use for all
# documents.
default_role = "py:obj"

# If true, '()' will be appended to :func: etc. cross-reference text.
#add_function_parentheses = True

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False


# -- Options for HTML output ----------------------------------------------

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['static']

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme_path = sphinx_bootstrap_theme.get_html_theme_path()
html_theme = 'bootstrap'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {
    "navbar_links": [
        ("Getting Started", "getting_started"),
        ("Configuration", "configuration"),
        ("Examples", "examples"),
        ("Plugins", "writing_plugins"),
        ("Release Notes", "releases"),
        ("Source Docs", "source_docs"),
    ],
    "navbar_class": "navbar",
    "globaltoc_includehidden": False,
    "navbar_sidebarrel": False,
    "navbar_pagenav": True,
    "source_link_position": False,
    "bootswatch_theme": "paper",
    "bootstrap_version": "3"
}
# html_theme_options = {
#     "description": "Resilient, adaptable service discovery.",
#     "logo": "lighthouse.png",
#     "logo_name": True,
#     "github_user": "wglass",
#     "github_repo": "lighthouse",
#     "github_banner": True,
#     "github_button": False,
#     "analytics_id": "UA-63292568-1",
#     "link": "#3782be",
#     "link_hover": "#3782be",
#     "note_bg": "#cfe7f8",
#     "pre_bg": "#eef7ff",
#     # "gray_1": "#fff",
#     "gray_2": "#fff",
#     # "gray_3": "#fff",
# }

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
#html_title = None

# A shorter title for the navigation bar.  Default is the same as html_title.
#html_short_title = None

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
#html_favicon = None

# Add any extra paths that contain custom files (such as robots.txt or
# .htaccess) here, relative to this directory. These files are copied
# directly to the root of the documentation.
#html_extra_path = []

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
#html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
#html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
# html_sidebars = {
#     '**': [
#         'about.html', 'navigation.html', 'searchbox.html', 'donate.html',
#     ]
# }


extlinks = {
    "current_tarball": (
        "https://pypi.python.org/packages/source/l/lighthouse/lighthouse-%s.tar.g%%s" % version,
        "lighthouse-%s.tar.g" % version
    )
}

# Additional templates that should be rendered to pages, maps page names to
# template names.
#html_additional_pages = {}

# If false, no module index is generated.
#html_domain_indices = True

# If false, no index is generated.
#html_use_index = True

# If true, the index is split into individual pages for each letter.
#html_split_index = False

html_show_sourcelink = False

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
#html_use_opensearch = ''

# This is the file name suffix for HTML files (e.g. ".xhtml").
#html_file_suffix = None

# Language to be used for generating the HTML full-text search index.
# Sphinx supports the following languages:
#   'da', 'de', 'en', 'es', 'fi', 'fr', 'hu', 'it', 'ja'
#   'nl', 'no', 'pt', 'ro', 'ru', 'sv', 'tr'
#html_search_language = 'en'

# A dictionary with options for the search language support, empty by default.
# Now only 'ja' uses this config value
#html_search_options = {'type': 'default'}

# The name of a javascript file (relative to the configuration directory) that
# implements a search results scorer. If empty, the default will be used.
#html_search_scorer = 'scorer.js'

# Output file base name for HTML help builder.
htmlhelp_basename = 'lighthousedoc'

# -- Options for LaTeX output ---------------------------------------------

latex_elements = {
# The paper size ('letterpaper' or 'a4paper').
#'papersize': 'letterpaper',

# The font size ('10pt', '11pt' or '12pt').
#'pointsize': '10pt',

# Additional stuff for the LaTeX preamble.
#'preamble': '',

# Latex figure (float) alignment
#'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
  (master_doc, 'lighthouse.tex', u'lighthouse Documentation',
   u'William Glass', 'manual'),
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
#latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
#latex_use_parts = False

# If true, show page references after internal links.
#latex_show_pagerefs = False

# If true, show URL addresses after external links.
#latex_show_urls = False

# Documents to append as an appendix to all manuals.
#latex_appendices = []

# If false, no module index is generated.
#latex_domain_indices = True


# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'lighthouse', u'lighthouse Documentation',
     [author], 1)
]

# If true, show URL addresses after external links.
#man_show_urls = False


# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
  (master_doc, 'lighthouse', u'lighthouse Documentation',
   author, 'lighthouse', 'One line description of project.',
   'Miscellaneous'),
]

# Documents to append as an appendix to all manuals.
#texinfo_appendices = []

# If false, no module index is generated.
#texinfo_domain_indices = True

# How to display URL addresses: 'footnote', 'no', or 'inline'.
#texinfo_show_urls = 'footnote'

# If true, do not generate a @detailmenu in the "Top" node's menu.
#texinfo_no_detailmenu = False
