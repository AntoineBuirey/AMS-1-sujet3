## Installation

> If you have previously installed this package, please clean the virtual environment with `pip uninstall -y -r <(pip freeze)` before proceeding.

To install the package in editable mode, run the following command in your terminal:
```bash
pip install -e .
pip install https://github.com/explosion/spacy-models/releases/download/fr_core_news_sm-3.8.0/fr_core_news_sm-3.8.0-py3-none-any.whl
```

## Usage

`networker [-h] [-v | -q | --level LEVEL] [--log-file FILE:LEVEL]
                 [--module-level MODULE:LEVEL] [--text INPUT_FILE]
                 [--dir INPUT_DIR] [--save-intermediate] [--save-graph-image]
                 [--show-vertices-labels] [--save-unknow-verb]
                 [--save-graphml]`

Tokenize a text file into sentences and words. a classic use will be `networker -gilm`. This will generate all graphs for the input texts, and save all intermediate data structures.

### options:
  - `-h`, `--help`
                        Show this help message and exit
  - `--text`, `-t` `INPUT_FILE`
                        Path to the input text file.
  - `--dir`, `-d` `INPUT_DIR`   
                        Path to a folder containing text to process.
  - `--save-intermediate`, `-i`
                        Save intermediate data structures to output directory.
  - `--save-graph-image`, `-g`
                        Save graph image to output directory.
  - `--show-vertices-labels`, `-l`
                        Show vertex labels on the saved graph image. Have no effect if `--save-graph-image` is not set.
  - `--save-unknow-verb`, `-u`
                        Store unknown verbs encountered during tagging to `output/unknown_verbs.txt`.
  - `--save-graphml`, `-m`
                        Save the graph in GraphML format to the output directory.

### logging:
  Logger configuration

  - `-v`, `--verbose`
  Increase verbosity level (default: 0), up to 2 (0 is `info`, 2 is `trace`)
  - `-q`, `--quiet`
  Decrease verbosity level (default: 0), up to 4 (0 is `info`, 4 is complely silent)
  - `--level` `LEVEL`
  Set the logging level. Format: `LEVEL`, where `LEVEL` is one of: `TRACE`, `DEBUG`, `INFO`, `WARNING`, `ERROR`, `FATAL`, `NONE`.
  - `--log-file` `FILE:LEVEL`
  Log to a file with a specific level (default: `info`).
  Format: `FILE:LEVEL`, where `LEVEL` is one of: `TRACE`, `DEBUG`, `INFO`, `WARNING`, `ERROR`, `FATAL`, `NONE`. Can be ommited to use the default level.You can specify multiple files.
  - `--module-level` `MODULE:LEVEL`
  Set the logging level for a specific module. If the name of the module doesn't exist, this do nothing.
  Format: `MODULE:LEVEL`, where `LEVEL` is one of: `TRACE`, `DEBUG`, `INFO`, `WARNING`, `ERROR`, `FATAL`, `NONE`.
