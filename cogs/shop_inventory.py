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

        raw_items = user.get("inventory", []) if user else []

        # 🔧 Normalize EVERYTHING into strings
        items = []

        for item in raw_items:

            # old broken format: {"name": "Sword"}
            if isinstance(item, dict):
                name = item.get("name")
                if name:
                    items.append(str(name))

            # correct format: "Sword"
            elif isinstance(item, str):
                items.append(item)

            # ignore anything else (prevents crashes)
            else:
                continue

        # 🧹 Remove duplicates + empty strings (optional cleanup)
        items = [i for i in items if i]
        items = list(dict.fromkeys(items))

        if not items:
            return await interaction.response.send_message("📦 Your inventory is empty.")

        embed = discord.Embed(
            title="🎒 Your Inventory",
            color=discord.Color.green()
        )

        embed.description = "\n".join([f"• {item}" for item in items])

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Inventory(bot))