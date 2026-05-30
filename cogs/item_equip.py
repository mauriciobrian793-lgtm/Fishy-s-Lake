import discord
from discord.ext import commands
from discord import app_commands
from pymongo import ReturnDocument


# =========================
# SELECT MENU (ITEM PICKER)
# =========================
class EquipSelect(discord.ui.Select):

    def __init__(self, items, shop_roles, user_inventory):

        options = []

        for item in items:
            if item["name"] in user_inventory:
                options.append(
                    discord.SelectOption(
                        label=item["name"],
                        description="Equip this item"
                    )
                )

        super().__init__(
            placeholder="Select an item to equip",
            options=options if options else [
                discord.SelectOption(label="No items", description="You own nothing", value="none")
            ]
        )

        self.shop_roles = shop_roles

    async def callback(self, interaction: discord.Interaction):

        if self.values[0] == "none":
            return await interaction.response.send_message("❌ You own no items.", ephemeral=True)

        item_name = self.values[0]

        data = await self.shop_roles.find_one({"guild_id": str(interaction.guild.id)})

        if not data:
            return await interaction.response.send_message("❌ No role mappings found.", ephemeral=True)

        role_id = data.get("items", {}).get(item_name)

        if not role_id:
            return await interaction.response.send_message("❌ This item has no role assigned.", ephemeral=True)

        role = interaction.guild.get_role(int(role_id))

        if not role:
            return await interaction.response.send_message("❌ Role not found.", ephemeral=True)

        await interaction.user.add_roles(role)

        await interaction.response.send_message(
            f"✅ Equipped **{item_name}** → {role.mention}",
            ephemeral=True
        )


# =========================
# VIEW
# =========================
class EquipView(discord.ui.View):

    def __init__(self, items, shop_roles, user_inventory):
        super().__init__(timeout=60)
        self.add_item(EquipSelect(items, shop_roles, user_inventory))


# =========================
# COG
# =========================
class Equip(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.economy = bot.economy
        self.shop_roles = bot.shop_roles

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

    @app_commands.command(name="equip", description="Equip an item from your inventory")
    async def equip(self, interaction: discord.Interaction):

        user = await self.get_user(
            interaction.guild.id,
            interaction.user.id,
            interaction.user.name
        )

        inventory = user.get("inventory", [])

        if not inventory:
            return await interaction.response.send_message(
                "❌ You have no items in your inventory.",
                ephemeral=True
            )

        shop_data = await self.bot.shop.find_one(
            {"guild_id": str(interaction.guild.id)}
        )

        if not shop_data or not shop_data.get("items"):
            return await interaction.response.send_message(
                "❌ No shop data found.",
                ephemeral=True
            )

        await interaction.response.send_message(
            "🎒 Choose an item to equip:",
            view=EquipView(
                shop_data["items"],
                self.shop_roles,
                inventory
            ),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Equip(bot))