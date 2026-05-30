import discord
from discord.ext import commands
from discord import app_commands
from pymongo import ReturnDocument


class Profile(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.economy = bot.economy

    # -------------------------
    # GET OR CREATE USER
    # -------------------------
    async def get_user(self, guild_id, user_id, name):
        return await self.economy.find_one_and_update(
            {"guild_id": str(guild_id), "user_id": str(user_id)},
            {
                "$setOnInsert": {
                    "guild_id": str(guild_id),
                    "user_id": str(user_id),
                    "name": name,
                    "balance": 0,  # wallet
                    "bank": 0
                }
            },
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

    # -------------------------
    # PROFILE COMMAND
    # -------------------------
    @app_commands.command(
        name="profile",
        description="View your full economy profile"
    )
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):

        if not interaction.guild:
            return await interaction.response.send_message("Guild only command.")

        # default to self
        if user is None:
            user = interaction.user

        data = await self.get_user(
            interaction.guild.id,
            user.id,
            user.name
        )

        wallet = data.get("balance", 0)
        bank = data.get("bank", 0)
        total = wallet + bank

        embed = discord.Embed(
            title="📊 Economy Profile",
            color=discord.Color.gold()
        )

        embed.set_thumbnail(url=user.display_avatar.url)

        embed.add_field(name="👤 User", value=user.mention, inline=False)
        embed.add_field(name="💰 Wallet", value=f"${wallet}", inline=True)
        embed.add_field(name="🏦 Bank", value=f"${bank}", inline=True)
        embed.add_field(name="🧾 Net Worth", value=f"${total}", inline=False)

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Profile(bot))