import discord
from discord.ext import commands
from discord import app_commands
import random
from utils import check_cooldown


class Crime(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.economy = bot.economy

    def get_user(self, guild_id, user_id, name):
        return self.economy.find_one_and_update(
            {"guild_id": str(guild_id), "user_id": str(user_id)},
            {
                "$setOnInsert": {
                    "guild_id": str(guild_id),
                    "user_id": str(user_id),
                    "name": name,
                    "balance": 0
                }
            },
            upsert=True,
            return_document=True
        )

    def update_balance(self, guild_id, user_id, amount):
        self.economy.update_one(
            {"guild_id": str(guild_id), "user_id": str(user_id)},
            {"$inc": {"balance": amount}}
        )

    @app_commands.command(name="crime", description="Commit a crime for money")
    async def crime(self, interaction: discord.Interaction):

        if not interaction.guild:
            return await interaction.response.send_message(
                "❌ This command only works in servers.",
                ephemeral=True
            )

        settings = self.bot.settings.setdefault(str(interaction.guild.id), {})

        allowed, remaining = check_cooldown(
            interaction.guild.id,
            interaction.user.id,
            "crime",
            settings
        )

        if not allowed:
            return await interaction.response.send_message(
                f"⏳ Wait {remaining}s before using this command again.",
                ephemeral=True
            )

        guild_id = interaction.guild.id
        user_id = interaction.user.id

        user = self.get_user(guild_id, user_id, interaction.user.name)

        success = random.randint(1, 100) <= 40

        if success:
            earnings = random.randint(100, 10000)
            self.update_balance(guild_id, user_id, earnings)

            msg = random.choice([
                "You robbed a bank vault 🏦",
                "You hacked an ATM 💻",
                "You stole a luxury car 🚗",
                "You robbed a jewelry store 💎",
            ])

            embed = discord.Embed(
                title="🚔 Crime Successful!",
                description=msg,
                color=discord.Color.green()
            )

            embed.add_field(name="💰 Earned", value=f"${earnings}", inline=True)

        else:
            loss = random.randint(1, 1000)

            current = user.get("balance", 0)
            loss = min(loss, current)

            self.update_balance(guild_id, user_id, -loss)

            msg = random.choice([
                "You got caught by the police 🚓",
                "Security stopped you 🛑",
                "You failed the robbery 💸",
                "You tripped while escaping 😭",
            ])

            embed = discord.Embed(
                title="❌ Crime Failed!",
                description=msg,
                color=discord.Color.red()
            )

            embed.add_field(name="💸 Lost", value=f"${loss}", inline=True)

        updated = self.get_user(guild_id, user_id, interaction.user.name)

        embed.add_field(
            name="🏦 Balance",
            value=f"${updated.get('balance', 0)}",
            inline=True
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Crime(bot))