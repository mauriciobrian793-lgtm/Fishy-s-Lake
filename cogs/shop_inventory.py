import discord
from discord.ext import commands
from discord import app_commands


class Inventory(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.economy = bot.economy

    @app_commands.command(name="inventory", description="View your items")
    async def inventory(self, interaction: discord.Interaction):

        user = await self.economy.find_one({
            "guild_id": str(interaction.guild.id),
            "user_id": str(interaction.user.id)
        })

        items = user.get("inventory", []) if user else []

        embed = discord.Embed(
            title="🎒 Inventory",
            color=discord.Color.green()
        )

        if not items:
            embed.description = "You own nothing."
        else:
            embed.description = "\n".join(
                [f"• {item['name']}" for item in items]
            )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Inventory(bot))