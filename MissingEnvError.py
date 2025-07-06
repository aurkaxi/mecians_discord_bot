class MissingEnvError(Exception):
    def __init__(self, *env_vars: str):
        """
        Exception raised when one or more required environment variables are missing.

        Args:
            *env_vars (str): Names of the missing environment variables.

        Example:
            >>> raise MissingEnvError('DISCORD_TOKEN', 'DATABASE_URL')
            Traceback (most recent call last):
                ...
            MissingEnvError: Missing required environment variable(s):
                DISCORD_TOKEN
                DATABASE_URL
        """
        super().__init__(
            f"Missing required environment variable(s):\n\t{'\n'.join(env_vars)}"
        )
