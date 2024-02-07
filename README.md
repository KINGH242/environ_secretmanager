# environ_secretmanager

The `environ_secretmanager` module is designed to be used to download Google Cloud Secrets Manager secrets and set them 
as environment variables. This is useful for using secrets in various environments, and works especially well with App 
Engine and Cloud Functions where the correct environment variables can be created in an env file during CI/CD and used 
in the final build files for production.


## Usage

```python
from environ_secretmanager.env_secrets import EnvironSecretManager

secrets = EnvironSecretManager(GOOGLE_CLOUD_PROJECT_ID="my-project-id")

# To create a .env file with the secrets
secrets.create_dot_env_file()

# To use the secrets in the current environment
MY_SECRET = secrets.get_env_secret("MY_SECRET", 1)
```

## Build For Local Distribution
Build the files then extract the setup.py file from the tarball and run it to install the package locally.
```shell
poetry build --format sdist
tar -xvf dist/*-`poetry version -s`.tar.gz -O '*/setup.py' > setup.py
```
Then on the machine you want to install the package on, run
```shell
pip install -e .
```

## Development

This project uses [Poetry](https://python-poetry.org/) in development to create a virtual environment and manage
dependencies.
To install poetry, run

```shell
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
```

Then, from the same directory as `pyproject.toml`, run

```shell
poetry install
```

Run `poetry` commands from this same directory to manage your development environment and/or setup the virtual environment created in the last step in your IDE.


See [Poetry Docs](https://python-poetry.org/docs/cli/) for more info.
