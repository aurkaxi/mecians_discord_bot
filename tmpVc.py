import discord
from discord import Interaction, app_commands
from discord.ext import commands

from bot import MecBot
from database.models import tmpVcSpawners


class TmpVcCog(commands.Cog):
    def __init__(self, bot: MecBot) -> None:
        super().__init__()
        self.bot = bot
        self.spawners = []
        self.spawner_ids: set[int] = set()

    async def fetch_spawners(self):
        """Get the list of spawners from the database."""
        # This is a placeholder for actual database logic
        res = await self.bot.db.select("tmpVcSpawners")
        self.spawners = [tmpVcSpawners(**item) for item in res]

        self.spawner_ids = {spawner.channel_id for spawner in self.spawners}
        return self.spawners

    async def register_tmpVc(self, channel_id: int, creator: int, spawner_id: int):
        """Register a new temporary voice channel spawner."""
        # This is a placeholder for actual database logic
        spawner = discord.utils.find(
            lambda s: s.channel_id == spawner_id, self.spawners
        )

        await self.bot.db.insert(
            "tmpVcs",
            {
                "channel_id": channel_id,
                "created_at": discord.utils.utcnow(),
                "creator": creator,
                "owner": creator,
                "spawner": spawner.id if spawner else None,
            },
        )
        return True

    async def unregister_tmpVc(self, channel_id: int):
        """Unregister a temporary voice channel."""
        # This is a placeholder for actual database logic
        res = await self.bot.db.query(
            "DELETE FROM tmpVcs WHERE channel_id = $channel_id",
            {"channel_id": channel_id},
        )
        return res

    async def is_channel_tmpVc(self, channel: discord.VoiceChannel) -> bool:
        """Check if a voice channel is a temporary voice channel."""
        # This is a placeholder for actual database logic
        res = await self.bot.db.query(
            "SELECT * FROM tmpVcs WHERE channel_id = $channel_id",
            {"channel_id": channel.id},
        )
        if isinstance(res, list):
            return len(res) > 0
        return False

    async def cog_load(self) -> None:
        """Load the cog and fetch spawners."""
        await self.fetch_spawners()
        print(f"Loaded {len(self.spawners)} temporary voice channel spawners.")
        return await super().cog_load()

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if member.bot:
            return

        if before.channel is after.channel:
            return

        if after.channel is not None:
            assert isinstance(after.channel, discord.VoiceChannel)
            # User joined a voice channel
            if after.channel.id in self.spawner_ids:
                # Create a new temporary voice channel
                guild = member.guild
                spawner_channel = after.channel

                # TODO: add permissions
                temp_channel = await guild.create_voice_channel(
                    name=f"{member.name}'s VC",
                    category=spawner_channel.category,
                )
                # print(f"after channel before creation: {after.channel.id}")

                await member.move_to(temp_channel)

                await self.register_tmpVc(
                    channel_id=temp_channel.id,
                    creator=member.id,
                    spawner_id=spawner_channel.id,
                )

        if before.channel is not None:
            assert isinstance(before.channel, discord.VoiceChannel)
            # User left a voice channel
            if (len(before.channel.members) == 0) and (
                await self.is_channel_tmpVc(before.channel)
            ):
                # Check if the channel is a temporary voice channel
                await self.unregister_tmpVc(before.channel.id)
                try:
                    await before.channel.delete()
                except discord.errors.NotFound:
                    pass

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        """Handle the deletion of a guild channel."""
        if not isinstance(channel, discord.VoiceChannel):
            return
        # Check if the channel is a temporary voice channel
        if await self.is_channel_tmpVc(channel):
            # Unregister the temporary voice channel
            await self.unregister_tmpVc(channel.id)

        if channel.id in self.spawner_ids:
            spawner_obj = discord.utils.find(
                lambda s: s.channel_id == channel.id, self.spawners
            )
            if spawner_obj:
                self.spawners.remove(spawner_obj)
            self.spawner_ids.remove(channel.id)

            await self.bot.db.query(
                "DELETE FROM tmpVcSpawners WHERE channel_id = $channel_id",
                {"channel_id": channel.id},
            )

    @app_commands.command()
    async def add_spawner(
        self, interaction: Interaction, channel: discord.VoiceChannel
    ):
        """Add a new temporary voice channel spawner."""
        # check if already a spawner
        if channel.id in self.spawner_ids:
            await interaction.response.send_message(
                f"{channel.name} is already a spawner.", ephemeral=True
            )
            return
        # Add the spawner to the database
        new_spawner = await self.bot.db.insert(
            "tmpVcSpawners",
            {
                "channel_id": channel.id,
                "created_at": discord.utils.utcnow(),
            },
        )
        # TODO: remove this after finally figuring out when dict, when list
        print(f"new_spawner type: {type(new_spawner)}")

        if isinstance(new_spawner, dict):
            new_spawner_obj = tmpVcSpawners(**new_spawner)
        else:
            new_spawner_obj = tmpVcSpawners(**new_spawner[0])

        # Update the local spawners list
        self.spawners.append(new_spawner_obj)
        self.spawner_ids.add(new_spawner_obj.channel_id)
        await interaction.response.send_message(
            f"Added {channel.name} as a temporary voice channel spawner."
        )
        return new_spawner_obj


async def setup(bot: MecBot) -> None:
    await bot.add_cog(TmpVcCog(bot))
