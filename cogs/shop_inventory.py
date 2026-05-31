import discord
from discord.ext import commands
from discord import app_commands


class Inventory(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.economy = bot.economy

    @app_commands.command(name="inventory", description="View your inventory")
    async def inventory(self, interaction: discord.Interaction):

        user = await self.economy.find_one({
            "guild_id": str(interaction.guild.id),
            "user_id": str(interaction.user.id)
        })

        if not user:
            return await interaction.response.send_message("📦 You have no data yet.")

        raw_items = user.get("inventory", [])

        if not raw_items:
            return await interaction.response.send_message("📦 Your inventory is empty.")

        # =========================
        # CLEAN INVENTORY (FIXED)
        # =========================
        clean_items = []

        for item in raw_items:

            # dict format: {"name": "..."}
            if isinstance(item, dict):
                name = item.get("name")
                if name:
                    clean_items.append(name)

            # string format: "item"
            elif isinstance(item, str):
                clean_items.append(item)

        # remove duplicates while keeping order
        clean_items = list(dict.fromkeys(clean_items))

        # =========================
        # EMBED
        # =========================
        embed = discord.Embed(
            title="🎒 Your Inventory",
            color=discord.Color.green()
        )

        embed.description = "\n".join(f"• {i}" for i in clean_items) or "Empty"

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Inventory(bot))