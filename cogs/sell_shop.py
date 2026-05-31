import discord
from discord.ext import commands


class SellView(discord.ui.View):

    def __init__(self, items, shop, economy):
        super().__init__(timeout=60)
        self.shop = shop
        self.economy = economy

        options = [
            discord.SelectOption(
                label=item["name"],
                value=item["item_id"]
            )
            for item in items
        ]

        self.select = discord.ui.Select(
            placeholder="Select item to sell",
            options=options
        )

        self.select.callback = self.sell_callback
        self.add_item(self.select)

    async def sell_callback(self, interaction: discord.Interaction):

        item_id = self.select.values[0]

        user = await self.economy.find_one({
            "guild_id": str(interaction.guild.id),
            "user_id": str(interaction.user.id)
        })

        if not user:
            return await interaction.response.send_message("❌ No data found.", ephemeral=True)

        inventory = user.get("inventory", [])

        # find item in inventory
        item = next((i for i in inventory if i["item_id"] == item_id), None)

        if not item:
            return await interaction.response.send_message("❌ You don't own this item.", ephemeral=True)

        # get shop price for value reference
        shop_data = await self.shop.find_one({"guild_id": str(interaction.guild.id)})

        shop_item = None
        if shop_data:
            shop_item = next((i for i in shop_data.get("items", []) if i["item_id"] == item_id), None)

        # fallback value
        sell_price = int(shop_item["price"] * 0.6) if shop_item else 100

        # remove item from inventory
        new_inventory = [i for i in inventory if i["item_id"] != item_id]

        await self.economy.update_one(
            {"guild_id": str(interaction.guild.id), "user_id": str(interaction.user.id)},
            {
                "$set": {"inventory": new_inventory},
                "$inc": {"balance": sell_price}
            }
        )

        await interaction.response.send_message(
            f"💰 Sold **{item['name']}** for **${sell_price}**!",
            ephemeral=True
        )


class Sell(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.economy = bot.economy
        self.shop = bot.shop

    @app_commands.command(name="sell", description="Sell items from your inventory")
    async def sell(self, interaction: discord.Interaction):

        user = await self.economy.find_one({
            "guild_id": str(interaction.guild.id),
            "user_id": str(interaction.user.id)
        })

        if not user or not user.get("inventory"):
            return await interaction.response.send_message(
                "❌ You have no items to sell.",
                ephemeral=True
            )

        await interaction.response.send_message(
            "Select an item to sell:",
            view=SellView(
                user["inventory"],
                self.shop,
                self.economy
            ),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Sell(bot))