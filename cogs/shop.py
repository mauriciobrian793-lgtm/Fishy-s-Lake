import discord
from discord.ext import commands
from discord import app_commands


class Shop(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.shop = bot.shop

    @app_commands.command(name="shop", description="View the shop")
    async def shop(self, interaction: discord.Interaction):

        data = await self.shop.find_one({"guild_id": str(interaction.guild.id)})

        embed = discord.Embed(
            title="🛒 Server Shop",
            color=discord.Color.blue()
        )

        if not data or not data.get("items"):
            embed.description = "No items available."
            return await interaction.response.send_message(embed=embed)

        for item in data["items"]:
            embed.add_field(
                name=item["name"],
                value=f"💰 ${item['price']}" + (f"\n🎁 Role: <@&{item['role']}>" if item.get("role") else ""),
                inline=False
            )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Shop(bot))