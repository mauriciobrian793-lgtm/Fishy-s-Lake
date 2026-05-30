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
            label=f"Buy {item['name']} (${item['price']})",
            style=discord.ButtonStyle.green
        )
        self.item = item
        self.economy = economy

    async def callback(self, interaction: discord.Interaction):

        user_id = interaction.user.id
        guild_id = interaction.guild.id

        user = await self.economy.find_one_and_update(
            {"guild_id": str(guild_id), "user_id": str(user_id)},
            {
                "$setOnInsert": {
                    "guild_id": str(guild_id),
                    "user_id": str(user_id),
                    "name": interaction.user.name,
                    "balance": 0,
                    "bank": 0,
                    "inventory": []
                }
            },
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

        balance = user.get("balance", 0)

        # ❌ not enough money
        if balance < self.item["price"]:
            return await interaction.response.send_message(
                "❌ You don’t have enough money.",
                ephemeral=True
            )

        # 💰 transaction
        await self.economy.update_one(
            {"guild_id": str(guild_id), "user_id": str(user_id)},
            {
                "$inc": {"balance": -self.item["price"]},
                "$push": {"inventory": self.item["name"]}
            }
        )

        await interaction.response.send_message(
            f"✅ You bought **{self.item['name']}**!",
            ephemeral=True
        )


# =========================
# SHOP VIEW (UI)
# =========================
class ShopView(discord.ui.View):

    def __init__(self, items, economy):
        super().__init__(timeout=None)

        for item in items:
            self.add_item(BuyButton(item, economy))


# =========================
# SHOP COMMAND
# =========================
class Shop(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.economy = bot.economy
        self.shop = bot.shop  # shop collection

    @app_commands.command(name="shop", description="Open the interactive shop")
    async def shop_cmd(self, interaction: discord.Interaction):

        if not interaction.guild:
            return await interaction.response.send_message("Guild only command.")

        shop_data = await self.shop.find_one({"guild_id": str(interaction.guild.id)})

        embed = discord.Embed(
            title="🛒 Server Shop",
            color=discord.Color.blue()
        )

        if not shop_data or not shop_data.get("items"):
            embed.description = "The shop is empty right now."
            return await interaction.response.send_message(embed=embed)

        for item in shop_data["items"]:
            embed.add_field(
                name=f"{item['name']} - ${item['price']}",
                value=item.get("description", "No description"),
                inline=False
            )

        view = ShopView(shop_data["items"], self.economy)

        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Shop(bot))