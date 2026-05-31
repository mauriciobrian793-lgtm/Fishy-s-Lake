import discord
from discord.ext import commands
from discord import app_commands


# =========================
# SELL VIEW
# =========================
class SellView(discord.ui.View):

    def __init__(self, bot, items):
        super().__init__(timeout=60)
        self.bot = bot

        options = []

        seen = set()

        for i in items:
            # normalize string OR dict
            if isinstance(i, dict):
                name = i.get("name")
            else:
                name = str(i)

            if not name:
                continue

            if name in seen:
                continue

            seen.add(name)

            options.append(
                discord.SelectOption(
                    label=name,
                    value=name
                )
            )

        if not options:
            options = [discord.SelectOption(label="No items", value="none")]

        self.select = discord.ui.Select(
            placeholder="Select item to sell",
            options=options
        )

        self.select.callback = self.sell_callback
        self.add_item(self.select)

    async def sell_callback(self, interaction: discord.Interaction):

        selected = self.select.values[0]

        if selected == "none":
            return await interaction.response.send_message("❌ Nothing to sell.", ephemeral=True)

        user = await self.bot.economy.find_one(
            {"guild_id": str(interaction.guild.id), "user_id": str(interaction.user.id)}
        )

        if not user:
            return await interaction.response.send_message("❌ No data found.", ephemeral=True)

        inventory = user.get("inventory", [])

        # normalize inventory check
        if selected not in inventory:
            return await interaction.response.send_message("❌ You don't own this item.", ephemeral=True)

        shop = await self.bot.shop.find_one({"guild_id": str(interaction.guild.id)})

        price = 0

        if shop and shop.get("items"):
            for i in shop["items"]:
                if i.get("name") == selected:
                    price = int(i.get("price", 0) * 0.5)
                    break

        await self.bot.economy.update_one(
            {"guild_id": str(interaction.guild.id), "user_id": str(interaction.user.id)},
            {
                "$pull": {"inventory": selected},
                "$inc": {"balance": price}
            }
        )

        await interaction.response.send_message(
            f"💰 Sold **{selected}** for **${price}**",
            ephemeral=True
        )


# =========================
# SELL COMMAND
# =========================
class Sell(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="sell", description="Sell items")
    async def sell(self, interaction: discord.Interaction):

        user = await self.bot.economy.find_one(
            {"guild_id": str(interaction.guild.id), "user_id": str(interaction.user.id)}
        )

        if not user or not user.get("inventory"):
            return await interaction.response.send_message("📦 Inventory empty.")

        await interaction.response.send_message(
            "💰 Select item to sell:",
            view=SellView(self.bot, user["inventory"]),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Sell(bot))