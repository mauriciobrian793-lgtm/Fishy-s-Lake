import discord
from discord.ext import commands
from discord import app_commands
from pymongo import ReturnDocument


# =========================
# BUY VIEW (DROPDOWN)
# =========================
class BuyView(discord.ui.View):

    def __init__(self, bot, items):
        super().__init__(timeout=60)
        self.bot = bot

        options = []

        for i in items:
            if not isinstance(i, dict):
                continue

            name = i.get("name")
            if not name:
                continue

            options.append(
                discord.SelectOption(
                    label=f"{name} - ${i.get('price', 0)}",
                    value=name[:100]
                )
            )

        if not options:
            options = [discord.SelectOption(label="No items", value="none")]

        self.select = discord.ui.Select(
            placeholder="Select an item to buy",
            options=options
        )

        self.select.callback = self.buy_callback
        self.add_item(self.select)

    async def buy_callback(self, interaction: discord.Interaction):

        selected = self.select.values[0]

        if selected == "none":
            return await interaction.response.send_message("❌ No items available.", ephemeral=True)

        shop = await self.bot.shop.find_one({"guild_id": str(interaction.guild.id)})

        if not shop or not shop.get("items"):
            return await interaction.response.send_message("❌ Shop empty.", ephemeral=True)

        item = next((i for i in shop["items"] if i.get("name") == selected), None)

        if not item:
            return await interaction.response.send_message("❌ Item not found.", ephemeral=True)

        user = await self.bot.economy.find_one_and_update(
            {"guild_id": str(interaction.guild.id), "user_id": str(interaction.user.id)},
            {
                "$setOnInsert": {
                    "guild_id": str(interaction.guild.id),
                    "user_id": str(interaction.user.id),
                    "name": interaction.user.name,
                    "balance": 0,
                    "bank": 0,
                    "inventory": []
                }
            },
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

        if user.get("balance", 0) < item["price"]:
            return await interaction.response.send_message("❌ Not enough money.", ephemeral=True)

        await self.bot.economy.update_one(
            {"guild_id": str(interaction.guild.id), "user_id": str(interaction.user.id)},
            {
                "$inc": {"balance": -item["price"]},
                "$push": {"inventory": item["name"]}
            }
        )

        # role give
        role_id = item.get("role_id")
        if role_id:
            role = interaction.guild.get_role(int(role_id))
            if role:
                await interaction.user.add_roles(role)

        await interaction.response.send_message(
            f"✅ Bought **{item['name']}** for **${item['price']}**!",
            ephemeral=True
        )


# =========================
# BUY COMMAND
# =========================
class Buy(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="buy", description="Buy from shop")
    async def buy(self, interaction: discord.Interaction):

        shop = await self.bot.shop.find_one({"guild_id": str(interaction.guild.id)})

        if not shop or not shop.get("items"):
            return await interaction.response.send_message("❌ Shop is empty.")

        await interaction.response.send_message(
            "🛒 Select an item to buy:",
            view=BuyView(self.bot, shop["items"]),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Buy(bot))