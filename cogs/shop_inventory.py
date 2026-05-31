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

        if not user or not user.get("inventory"):
            return await interaction.response.send_message("📦 Your inventory is empty.")

        raw_items = user.get("inventory", [])

        # 🔧 FIX: support BOTH formats (string + dict)
        items = []
        for item in raw_items:
            if isinstance(item, dict):
                items.append(item.get("name", "Unknown Item"))
            else:
                items.append(str(item))

        embed = discord.Embed(
            title="🎒 Your Inventory",
            color=discord.Color.green()
        )

        embed.description = "\n".join([f"• {i}" for i in items]) or "Empty"

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Inventory(bot))