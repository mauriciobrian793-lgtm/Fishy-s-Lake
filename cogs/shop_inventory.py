import discord
from discord.ext import commands
from discord import app_commands
from pymongo import ReturnDocument


class Inventory(commands.Cog):

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
                    "balance": 0,
                    "bank": 0,
                    "inventory": []
                }
            },
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

    # -------------------------
    # INVENTORY COMMAND
    # -------------------------
    @app_commands.command(
        name="inventory",
        description="View your owned items"
    )
    async def inventory(self, interaction: discord.Interaction, user: discord.Member = None):

        if not interaction.guild:
            return await interaction.response.send_message("Guild only command.")

        if user is None:
            user = interaction.user

        data = await self.get_user(
            interaction.guild.id,
            user.id,
            user.name
        )

        inventory = data.get("inventory", [])

        embed = discord.Embed(
            title="🎒 Inventory",
            color=discord.Color.gold()
        )

        embed.set_thumbnail(url=user.display_avatar.url)

        embed.add_field(
            name="👤 User",
            value=user.mention,
            inline=False
        )

        # -------------------------
        # EMPTY INVENTORY
        # -------------------------
        if not inventory:
            embed.description = "You don't own any items yet."
        else:
            # format items nicely
            item_list = "\n".join([f"• {item}" for item in inventory])

            embed.add_field(
                name="📦 Items Owned",
                value=item_list,
                inline=False
            )

            embed.add_field(
                name="🔢 Total Items",
                value=str(len(inventory)),
                inline=False
            )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Inventory(bot))