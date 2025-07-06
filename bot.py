import asyncio
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv
from surrealdb import (
    AsyncHttpSurrealConnection,
    AsyncSurreal,
    AsyncWsSurrealConnection,
)

from MissingEnvError import MissingEnvError


class MecBot(commands.Bot):
    def __init__(
        self, db: AsyncWsSurrealConnection | AsyncHttpSurrealConnection
    ) -> None:
        super().__init__(
            command_prefix=commands.when_mentioned_or("!"),
            # help_command=help_command,
            # tree_cls=tree_cls,
            # descriptionb=description,
            # allowed_contexts=allowed_contexts,
            # allowed_installs=allowed_installs,
            intents=discord.Intents.all(),
            activity=discord.Activity(
                name="Status Message",
                type=discord.ActivityType.custom,
                state=os.getenv("DISCORD_STATUS"),
            ),
        )
        self.db = db

    async def setup_hook(self) -> None:
        extensions = [
            "jishaku",
        ]

        for ext in extensions:
            try:
                await self.load_extension(ext)
            except Exception as e:
                print(f"Failed to load extension {ext}: {e}")

        return await super().setup_hook()


async def run():
    db_url = os.getenv("SURREALDB_URL")
    db_ns = os.getenv("SURREALDB_NAMESPACE")
    db_db = os.getenv("SURREALDB_DATABASE")
    db_username = os.getenv("SURREALDB_USERNAME")
    db_password = os.getenv("SURREALDB_PASSWORD")

    # if not db_ns or not db_db:
    if not all([db_url, db_ns, db_db, db_username, db_password]):
        raise MissingEnvError(
            "SURREALDB_URL",
            "SURREALDB_NAMESPACE",
            "SURREALDB_DATABASE",
            "SURREALDB_USERNAME",
            "SURREALDB_PASSWORD",
        )

    async with AsyncSurreal(db_url) as db:
        await db.signin(
            {
                "username": db_username,
                "password": db_password,
                "namespace": db_ns,
                "database": db_db,
            }
        )

        token = os.getenv("DISCORD_TOKEN")
        if not token:
            raise MissingEnvError("DISCORD_TOKEN")
        await MecBot(db).start(token=token)


if __name__ == "__main__":
    load_dotenv()
    discord.utils.setup_logging()
    asyncio.run(run())
