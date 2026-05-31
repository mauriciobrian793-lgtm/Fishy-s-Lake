import discord
from discord.ext import commands
from discord import app_commands


class Buy(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.economy = bot.economy
        self.shop = bot.shop

    @app_commands.command(name="buy", description="Buy an item from the shop")
    async def buy(self, interaction: discord.Interaction, item_name: str):

        shop_data = await self.shop.find_one({"guild_id": str(interaction.guild.id)})

        if not shop_data or not shop_data.get("items"):
            return await interaction.response.send_message("❌ Shop is empty.")

        item = next(
            (i for i in shop_data["items"]
             if i["name"].lower() == item_name.lower()),
            None
        )

        if not item:
            return await interaction.response.send_message("❌ Item not found.")

        user = await self.economy.find_one_and_update(
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
            return_document=True
        )

        if user.get("balance", 0) < item["price"]:
            return await interaction.response.send_message("❌ Not enough money.")

        # subtract + add item
        await self.economy.update_one(
            {"guild_id": str(interaction.guild.id), "user_id": str(interaction.user.id)},
            {
                "$inc": {"balance": -item["price"]},
                "$push": {"inventory": item["name"]}
            }
        )

        # role give
        if item.get("role_id"):
            role = interaction.guild.get_role(int(item["role_id"]))
            if role:
                await interaction.user.add_roles(role)

        await interaction.response.send_message(f"✅ Bought **{item['name']}**!")

async def setup(bot):
    await bot.add_cog(Buy(bot))