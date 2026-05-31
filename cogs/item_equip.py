import discord
from discord.ext import commands
from discord import app_commands


class EquipView(discord.ui.View):

    def __init__(self, items, shop, user_id, guild_id):
        super().__init__(timeout=60)
        self.shop = shop
        self.user_id = user_id
        self.guild_id = guild_id

        options = [
            discord.SelectOption(label=item["name"], value=item["item_id"])
            for item in items
        ]

        self.select = discord.ui.Select(
            placeholder="Choose item to equip",
            options=options
        )

        self.select.callback = self.callback
        self.add_item(self.select)

    async def callback(self, interaction: discord.Interaction):

        item_id = self.select.values[0]

        shop_data = await self.shop.find_one({"guild_id": str(interaction.guild.id)})

        item = next(
            (i for i in shop_data["items"] if i["item_id"] == item_id),
            None
        )

        if not item or not item.get("role_id"):
            return await interaction.response.send_message(
                "❌ This item has no role.",
                ephemeral=True
            )

        role = interaction.guild.get_role(int(item["role_id"]))

        if not role:
            return await interaction.response.send_message(
                "❌ Role not found.",
                ephemeral=True
            )

        await interaction.user.add_roles(role)

        await interaction.response.send_message(
            f"✅ Equipped **{item['name']}**!",
            ephemeral=True
        )


class Equip(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.economy = bot.economy
        self.shop = bot.shop

    @app_commands.command(name="equip", description="Equip an item")
    async def equip(self, interaction: discord.Interaction):

        user = await self.economy.find_one({
            "guild_id": str(interaction.guild.id),
            "user_id": str(interaction.user.id)
        })

        if not user or not user.get("inventory"):
            return await interaction.response.send_message(
                "❌ You own no items."
            )

        await interaction.response.send_message(
            "Select an item to equip:",
            view=EquipView(
                user["inventory"],
                self.shop,
                interaction.user.id,
                interaction.guild.id
            ),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Equip(bot))