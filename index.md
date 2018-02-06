---
title: "Py-Beams"
description: "Python-based minimal markup language for Beamer"
---
# What's this?

Py-Beams is a markup language for creating PDF slide shows from simple, easy to understand text files.

Please note: the language, its interpreter, as well as this very page, are currently under active and heavy development. This makes right now the perfect time to suggest features and discover problems (after I publish the repo, of course).

# Using the interpreter

## Installation

Currently the program is in an early stage of development and has not been published to PyPI, please [download a copy from Github](https://github.com/teonistor/py-beams/zipball/master) and run the package locally: `python -m pybeams`

## Configuration

TBC

## Dependencies

The interpreter requires at least Python 3.5 and has the following packages:
- ply
- yaml
- docopt
- PIL (for certain more advanced image arrangement features)

The first 2 are included in the standard Anaconda installation; `docopt` can be installed using pip.



# Language specification

## Document structure

At the outmost level of an input file reside 4 types of elements:

1. **Slides** are delimited by opening and closing square brackets, placed at the very beginning of lines of text (with no white space). An optional slide title can be given after the opening bracket.

    Example:
    ```
     [ Overview
      In this presentation we will be talking about this and that.
     ]
    ```
    
    Shrink (`.<number>`) or break (`...`) options can be specified immediately after the opening square bracket; these are useful when a slide has too much content to fit in under default settings.

    Examples:
    ```
     [... Long slide
      If this text is too long, it will be split across multiple slides.
     ]
     [.20
      This slide has no title, but its text will be 20% smaller than usual.
     ]
    ```

1. **Headings** are given outside by following a line of text with a streak of one of the symbols `- _ = ~` repeated at least 4 times. Headings should be surrounded by a visibly empty line before and after. The symbols will be understood to define sections, subsections, and subsubsections in the order in which they are encountered. 

    Example:
    ```
      Introduction
      ----
      
      Section about animals
      ----
      
      Subsection about cats
      ~~~~
    ```

1. **Configuration** can be given in the form of Yaml as described above. It will override default (and user-wide) configuration.

    Example:
    ```
     theme: Berkeley
     scheme: beetle
    ```

1. Any other text which does not fall into the first 2 categories and is not valid Yaml will be ignored.


## Slide structure

1. **Plain text**: Just write it. Paragraphs need to be separated by an empty line, as per LaTeX convention. Be aware of the structures below, as your text can be interpreted as one of them.

    Example:
    ```
      This is a paragraph.
      
      This is another paragraph.
    ```

1. **Text highlighting** is achieved by surrounding the highlighted text in groups of up to 4 asterisks. By default, the 4 levels of highlighting are: italics, bold, underlined, red coloured; but can be modified in the configuration (*there is currently a known bug around this feature*).

    Example:
    ```
      **Bold text**
      
      ***Underlined text***
    ```

1. **URLs** can be made clickable by surrounding them in square brackets; they should be on a single line.

    Example:
    ```
      [www.example.com]
    ```

1. **Text stretching and alignment**:
    ```
      [>Right-aligned text>]
      
      [>Centred text<]
      
      [<Left-aligned text (redundant by default, but relevant if justification to both sides set)<]
      
      [<Text stretched across whole slide width>]
      
      [vText pushed to the bottom (coming soon)v]
      
      etc.
    ```
    
    Suggestions are welcome as to what stranger combination of arrows (e.g. `[^ ... >]`) should do.

1. **Columns** are begun by a vertical bar, followed optionally by a width specifier which can be absolute (e.g. `10em`, `60pt`), relative to slide width (e.g. `35%`), or relative to other columns (e.g. `7`); in the third case, columns will split between themselves, proportionally with their numbers, the space unclaimed by columns in the second cases. Columns without a width specifier will split equally between them the space unclaimed by columns in the second case, therefore they do not make sense in the same context as columns in the third case. Column contents follow on subsequent lines and must be indented relative to the column marker (vertical bar). Multiple column environments can exist on the same slide, as well as columns inside columns, although that is a rather strange use case.

    Examples:
    ```
      [
	  Text before the columns
      
      |30%
	    This is a narrow column on the left
		
	  |
	    This is a wide column on the right
		
	  Text after the columns
	  ]
	  
      [
      |1
	    First column
		
	  |4
	    Second column, which is 4 times as wide as the first
	  ]
    ```

1. Lists

1. Boxes

1. Images

1. Footnotes, endnotes (coming soon)

1. Document concatenation (coming soon)

1. Verbatim text (coming soon)

1. **Special characters and escaping**. Special characters will generally go through unaltered, unless they form part of structures described here. Any character can be escaped by adding a backslash (`\`) before it.

1. **Native LaTeX commands** can be inserted if more advanced behaviour is desired, taking care to escape characters which form part of structures described here. Extra packages can be added to the configuration to be included at the beginning. Beware of potential clashes between custom commands and packages and those used and generated by the program.

1. Macros (coming later)

1. Integration with Plus (coming later)

## Comments

At any point in the document comments can be given by using the hash symbol `#`. Should this symbol be actually required in the document, it can be escaped: `\#`. Note that comments do not work inside structures which expect a beginning and an ending marker on the same line (think of this as a `#` symbol inside a string literal in a conventional programming language); there currently also exist some other known peculiarities regarding the implementation of comments.

# Full document examples

You can [download these examples from the repository](https://github.com/teonistor/py-beams/tree/examples) when they become available.
