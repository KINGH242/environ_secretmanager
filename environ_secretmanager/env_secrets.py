"""
Environments secrets manager
"""

import logging
import os
from pathlib import Path
from typing import List

import environ
from google.cloud import secretmanager

__all__ = ["EnvironSecretManager"]


class EnvironSecretManager:
    """
    Class to handle the retrieval of secrets from Google Secret Manager
    """

    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.logger = logging.getLogger(__name__)

        self.env = environ.Env()
        environ.Env.read_env()

        self.environment = kwargs.get("environment")
        self.filter = kwargs.get("filter")

        try:
            # Create the Secret Manager client.
            self.client = secretmanager.SecretManagerServiceClient()
            self.GOOGLE_CLOUD_PROJECT_ID = kwargs["GOOGLE_CLOUD_PROJECT_ID"]
            self.parent = f"projects/{self.GOOGLE_CLOUD_PROJECT_ID}"
            self.secrets = []
        except Exception as e:
            self.logger.error(e)

    def get_env_secret(self, secret_id: str, version_id: str) -> str:
        """
        Attempt to get secret from the environment then .env file. If unsuccessful, query Google Secret Manager.

        Args:
            secret_id (str): The ID of the secret.
            version_id (str): The version of the secret.
        Returns:
            str: The secret value.
        """
        secret = os.getenv(secret_id, self.env(secret_id, default=None))

        if secret is None:
            return self.access_secret_version(secret_id, version_id)
        else:
            return secret

    def access_secret_version(self, secret_id: str, version_id: str) -> str | None:
        """
        Access the payload for the given secret version if one exists. The version
        can be a version number as a string (e.g. "5") or an alias (e.g. "latest").

        Args:
            secret_id (str): The ID of the secret.
            version_id (str): The version of the secret.
        Returns:
            str: The secret value or None if an error occurs.
        """

        # Build the resource name of the secret version.
        name = f"{self.parent}/secrets/{secret_id}/versions/{version_id}"

        try:
            # Access the secret version.
            response = self.client.access_secret_version(request={"name": name})

            payload = response.payload.data.decode("UTF-8")
            return payload
        except Exception as e:
            self.logger.error(e)

    def list_secrets(self) -> List[str]:
        """
        List all secrets in the project.

        Returns:
            List[str]: List of secret names.
        """

        request = {"parent": self.parent}

        if self.filter:
            request["filter"] = self.filter

        if self.environment:
            if self.filter:
                request["filter"] += f" OR labels.environment={self.environment}"
            else:
                request["filter"] = f"labels.environment={self.environment}"

        # List all secrets.
        for secret in self.client.list_secrets(request=request):
            name = secret.name.split("/")[-1]
            self.secrets.append(name)
        return self.secrets

    def write_env_file(self, secrets_list: List[str], path: Path = None):
        """
        Write secrets to a .env file.

        Args:
            secrets_list (List[str]): List of secret names to write to the .env file.
            path (Path, optional): Path to the .env file. Defaults to None, which uses ".env".
        """
        env_path = path or ".env"

        with open(env_path, "w") as file:
            for secret in secrets_list:
                try:
                    secret_value = self.access_secret_version(secret, "latest")
                    file.write(f"{secret}='{secret_value}'\n")
                except Exception as e:
                    self.logger.error(f"Failed to create secret for: {secret}")
                    self.logger.error(e)

    def create_dot_env_file(self, path: Path = None):
        """
        Create a .env file with all secrets from Google Secret Manager.

        Args:
            path (Path, optional): Path to the .env file. Defaults to None, which uses ".env".
        """
        secrets_list = self.list_secrets()
        self.write_env_file(secrets_list, path)
