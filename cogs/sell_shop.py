import discord
from discord.ext import commands
from discord import app_commands


class SellView(discord.ui.View):

    def __init__(self, bot, items):
        super().__init__(timeout=60)
        self.bot = bot

        # ✅ SAFE: only handle string-based inventory items
        options = []

        for item in items:
            if isinstance(item, str):
                options.append(
                    discord.SelectOption(
                        label=item,
                        value=item
                    )
                )
            elif isinstance(item, dict):
                name = item.get("name")
                if name:
                    options.append(
                        discord.SelectOption(
                            label=name,
                            value=name
                        )
                    )

        self.select = discord.ui.Select(
            placeholder="Select item to sell",
            options=options if options else [
                discord.SelectOption(label="No items", value="none")
            ]
        )

        self.select.callback = self.sell_callback
        self.add_item(self.select)

    async def sell_callback(self, interaction: discord.Interaction):

        if self.select.values[0] == "none":
            return await interaction.response.send_message("❌ Nothing to sell.", ephemeral=True)

        item_name = self.select.values[0]

        user = await self.bot.economy.find_one({
            "guild_id": str(interaction.guild.id),
            "user_id": str(interaction.user.id)
        })

        if not user or item_name not in user.get("inventory", []):
            return await interaction.response.send_message("❌ You don’t own this item.", ephemeral=True)

        # 💰 find item in shop for price
        shop = await self.bot.shop.find_one({"guild_id": str(interaction.guild.id)})

        price = 0
        if shop and shop.get("items"):
            for i in shop["items"]:
                if i["name"].lower() == item_name.lower():
                    price = int(i["price"] * 0.5)  # sell = 50%
                    break

        # remove item
        await self.bot.economy.update_one(
            {"guild_id": str(interaction.guild.id), "user_id": str(interaction.user.id)},
            {
                "$pull": {"inventory": item_name},
                "$inc": {"balance": price}
            }
        )

        await interaction.response.send_message(
            f"💰 Sold **{item_name}** for **${price}**!",
            ephemeral=True
        )


class Sell(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.economy = bot.economy

    @app_commands.command(name="sell", description="Sell items from your inventory")
    async def sell(self, interaction: discord.Interaction):

        user = await self.economy.find_one({
            "guild_id": str(interaction.guild.id),
            "user_id": str(interaction.user.id)
        })

        if not user or not user.get("inventory"):
            return await interaction.response.send_message("📦 You have nothing to sell.")

        items = user.get("inventory", [])

        await interaction.response.send_message(
            "💰 Choose an item to sell:",
            view=SellView(self.bot, items),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Sell(bot))