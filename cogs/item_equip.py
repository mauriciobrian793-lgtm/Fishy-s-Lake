import discord
from discord.ext import commands
from discord import app_commands
from pymongo import ReturnDocument


# =========================
# DROPDOWN
# =========================
class EquipSelect(discord.ui.Select):

    def __init__(self, items, user_inventory):

        options = []

        for item in items:
            if item["name"] in user_inventory:
                options.append(
                    discord.SelectOption(
                        label=item["name"],
                        description="Equip this item"
                    )
                )

        if not options:
            options = [
                discord.SelectOption(
                    label="No items",
                    description="You don't own anything",
                    value="none"
                )
            ]

        super().__init__(
            placeholder="Select item to equip",
            options=options
        )

        self.items = items

    async def callback(self, interaction: discord.Interaction):

        if self.values[0] == "none":
            return await interaction.response.send_message("❌ You own no items.", ephemeral=True)

        item_name = self.values[0]

        # find item in shop
        item = next((i for i in self.items if i["name"] == item_name), None)

        if not item:
            return await interaction.response.send_message("❌ Item not found.", ephemeral=True)

        if not item.get("role"):
            return await interaction.response.send_message("❌ This item has no role.", ephemeral=True)

        role = interaction.guild.get_role(int(item["role"]))

        if not role:
            return await interaction.response.send_message("❌ Role missing or deleted.", ephemeral=True)

        await interaction.user.add_roles(role)

        await interaction.response.send_message(
            f"✅ Equipped **{item_name}** → {role.mention}",
            ephemeral=True
        )


# =========================
# VIEW
# =========================
class EquipView(discord.ui.View):

    def __init__(self, items, inventory):
        super().__init__(timeout=60)
        self.add_item(EquipSelect(items, inventory))


# =========================
# COG
# =========================
class Equip(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.economy = bot.economy
        self.shop = bot.shop

    async def get_user(self, guild_id, user_id, name):
        return await self.economy.find_one_and_update(
            {"guild_id": str(guild_id), "user_id": str(user_id)},
            {
                "$setOnInsert": {
                    "guild_id": str(guild_id),
                    "user_id": str(user_id),
                    "name": name,
                    "balance": 0,
                    "bank": 0,
                    "inventory": []
                }
            },
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

    @app_commands.command(name="equip", description="Equip an item")
    async def equip(self, interaction: discord.Interaction):

        user = await self.get_user(
            interaction.guild.id,
            interaction.user.id,
            interaction.user.name
        )

        inventory = user.get("inventory", [])

        if not inventory:
            return await interaction.response.send_message(
                "❌ You have no items.",
                ephemeral=True
            )

        shop_data = await self.shop.find_one({"guild_id": str(interaction.guild.id)})

        if not shop_data or not shop_data.get("items"):
            return await interaction.response.send_message(
                "❌ Shop is empty.",
                ephemeral=True
            )

        await interaction.response.send_message(
            "🎒 Choose an item to equip:",
            view=EquipView(shop_data["items"], inventory),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Equip(bot))