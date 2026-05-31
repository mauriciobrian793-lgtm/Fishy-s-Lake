import discord
from discord.ext import commands
from discord import app_commands


class Shop(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.shop = bot.shop

    @app_commands.command(name="shop")
    async def shop_cmd(self, interaction: discord.Interaction):

        data = await self.shop.find_one({"guild_id": str(interaction.guild.id)})

        embed = discord.Embed(
            title="🛒 Server Shop",
            color=discord.Color.blue()
        )

        if not data or not data.get("items"):
            embed.description = "Shop is empty."
            return await interaction.response.send_message(embed=embed)

        for item in data["items"]:

            role_text = f"<@&{item['role_id']}>" if item.get("role_id") else "No role"

            embed.add_field(
                name=f"{item['name']} - ${item['price']}",
                value=f"🎭 Role: {role_text}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Shop(bot))