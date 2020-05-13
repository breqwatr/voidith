# Voithos - Private Cloud Helper by Breqwatr

Voithos is a free and Open-Source utility written by Breqwatr to deploy and
manage private clouds. Breqwatr uses this tool internally and has open-sourced
it in the spirit of sharing and collaboration.


## Installation

Voithos is currently pre-release and only available on GitHub.

```bash
# Create virtualenv
virtualenv --python=python3 env/
source env/bin/activate

# Install voithos
pip install git+https://github.com/breqwatr/voithos.git
```



## For Developers

### Environment variables

```bash
# Enable dev mode
export VOITHOS_DEV=true

# Overwrite image code with local code
export ARCUS_API_DIR=<path to api checkout>
export ARCUS_CLIENT_DIR=<path to client checkout>
```

### Running the tests

```bash
# Quickly run unit tests
python -m pytest test/

# Run unit tests with tox
tox -e test

# show test coverage
text -e coverage

# Run linter
tox -e lint
```

### Applying the styles

Use Black to enforce the style guide. Its configuration is in `./pyproject.toml`

```bash
# Example of re-styling one file
black voithos\cli\main.py

# Example of re-styling the whole project
black voithos
```
