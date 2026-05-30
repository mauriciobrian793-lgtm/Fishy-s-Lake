import discord
from discord.ext import commands
from discord import app_commands
from pymongo import ReturnDocument


# =========================
# BUY SELECT MENU
# =========================
class BuySelect(discord.ui.Select):

    def __init__(self, items):
        options = []

        for item in items:
            options.append(
                discord.SelectOption(
                    label=item["name"],
                    description=f"${item['price']}"
                )
            )

        super().__init__(
            placeholder="Select an item to buy",
            options=options
        )

        self.items = items

    async def callback(self, interaction: discord.Interaction):

        chosen = None

        for item in self.items:
            if item["name"] == self.values[0]:
                chosen = item
                break

        if not chosen:
            return await interaction.response.send_message("❌ Item not found.", ephemeral=True)

        economy = interaction.client.economy

        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)

        user = await economy.find_one_and_update(
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

        if user.get("balance", 0) < chosen["price"]:
            return await interaction.response.send_message("❌ Not enough money.", ephemeral=True)

        await economy.update_one(
            {"guild_id": guild_id, "user_id": user_id},
            {
                "$inc": {"balance": -chosen["price"]},
                "$push": {"inventory": chosen["name"]}
            }
        )

        await interaction.response.send_message(
            f"✅ Bought **{chosen['name']}** for ${chosen['price']}!",
            ephemeral=True
        )


# =========================
# VIEW
# =========================
class BuyView(discord.ui.View):

    def __init__(self, items):
        super().__init__(timeout=60)
        self.add_item(BuySelect(items))


# =========================
# BUY COMMAND
# =========================
class Buy(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.shop = bot.shop

    @app_commands.command(name="buy", description="Buy an item from the shop")
    async def buy(self, interaction: discord.Interaction):

        data = await self.shop.find_one({"guild_id": str(interaction.guild.id)})

        if not data or not data.get("items"):
            return await interaction.response.send_message("❌ Shop is empty.", ephemeral=True)

        embed = discord.Embed(
            title="🛒 Select Item to Buy",
            description="Choose an item from the dropdown below.",
            color=discord.Color.green()
        )

        await interaction.response.send_message(
            embed=embed,
            view=BuyView(data["items"]),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Buy(bot))