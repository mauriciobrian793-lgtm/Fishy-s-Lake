import discord
from discord.ext import commands
from discord import app_commands
from pymongo import ReturnDocument


# =========================
# BUY BUTTON
# =========================
class BuyButton(discord.ui.Button):

    def __init__(self, item, economy):
        super().__init__(
            label=f"{item['name']} (${item['price']})",
            style=discord.ButtonStyle.green
        )
        self.item = item
        self.economy = economy

    async def callback(self, interaction: discord.Interaction):

        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)

        user = await self.economy.find_one_and_update(
            {"guild_id": guild_id, "user_id": user_id},
            {
                "$setOnInsert": {
                    "guild_id": guild_id,
                    "user_id": user_id,
                    "name": interaction.user.name,
                    "balance": 0,
                    "bank": 0,
                    "inventory": []
                }
            },
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

        if user.get("balance", 0) < self.item["price"]:
            return await interaction.response.send_message("❌ Not enough money.", ephemeral=True)

        await self.economy.update_one(
            {"guild_id": guild_id, "user_id": user_id},
            {
                "$inc": {"balance": -self.item["price"]},
                "$push": {"inventory": self.item["name"]}
            }
        )

        await interaction.response.send_message(
            f"✅ Bought **{self.item['name']}**!",
            ephemeral=True
        )


# =========================
# SHOP VIEW
# =========================
class ShopView(discord.ui.View):

    def __init__(self, items, economy):
        super().__init__(timeout=None)

        for item in items:
            self.add_item(BuyButton(item, economy))


# =========================
# SHOP COG
# =========================
class Shop(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.economy = bot.economy
        self.shop = bot.shop

    @app_commands.command(name="shop", description="Open shop")
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
            embed.add_field(
                name=item["name"],
                value=f"${item['price']}",
                inline=False
            )

        await interaction.response.send_message(
            embed=embed,
            view=ShopView(data["items"], self.economy)
        )


async def setup(bot):
    await bot.add_cog(Shop(bot))