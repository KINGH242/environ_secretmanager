"""
Environments secrets manager
"""
import logging

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

        try:
            # Create the Secret Manager client.
            self.client = secretmanager.SecretManagerServiceClient()
            self.GOOGLE_CLOUD_PROJECT_ID = kwargs["GOOGLE_CLOUD_PROJECT_ID"]
            self.secrets = []
        except Exception as e:
            self.logger.error(e)

    def get_env_secret(self, secret_id, version_id):
        """
        Attempt to get secret from environment. If unsuccessful, query Google Secret Manager
        """
        secret = self.env(secret_id, default=None)

        if secret is None:
            return self.access_secret_version(secret_id, version_id)
        else:
            return secret

    def access_secret_version(self, secret_id, version_id):
        """
        Access the payload for the given secret version if one exists. The version
        can be a version number as a string (e.g. "5") or an alias (e.g. "latest").
        """

        # Build the resource name of the secret version.
        name = f"projects/{self.GOOGLE_CLOUD_PROJECT_ID}/secrets/{secret_id}/versions/{version_id}"

        try:
            # Access the secret version.
            response = self.client.access_secret_version(request={"name": name})

            payload = response.payload.data.decode("UTF-8")
            return payload
        except Exception as e:
            self.logger.error(e)

    def list_secrets(self):
        """
        List all secrets in the project.
        """
        # Build the resource name of the parent project.
        parent = f"projects/{self.GOOGLE_CLOUD_PROJECT_ID}"

        # List all secrets.
        for secret in self.client.list_secrets(request={"parent": parent}):
            name = secret.name.split("/")[-1]
            self.secrets.append(name)
        return self.secrets

    def write_env_file(self, secrets_list):
        with open(".env", "w") as file:
            for secret in secrets_list:
                try:
                    secret_value = self.access_secret_version(secret, "latest")
                    file.write(f"{secret}='{secret_value}'\n")
                except Exception as e:
                    self.logger.error(f"Failed to create secret for: {secret}")
                    self.logger.error(e)

    def create_dot_env_file(self):
        secrets_list = self.list_secrets()
        self.write_env_file(secrets_list)
