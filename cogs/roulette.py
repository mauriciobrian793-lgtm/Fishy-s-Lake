import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
from utils import check_cooldown
from pymongo import ReturnDocument


RED_NUMBERS = {
    1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36
}

BLACK_NUMBERS = {
    2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35
}


def get_color(num):
    if num == 0:
        return "green"
    if num in RED_NUMBERS:
        return "red"
    return "black"


class Roulette(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.economy = bot.economy

    # =========================
    # USER SYSTEM
    # =========================
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
            return_document=ReturnDocument.AFTER
        )

    def update_balance(self, guild_id, user_id, amount):
        self.economy.update_one(
            {"guild_id": str(guild_id), "user_id": str(user_id)},
            {"$inc": {"balance": amount}}
        )

    # =========================
    # COMMAND
    # =========================
    @app_commands.command(
        name="roulette",
        description="Bet on roulette (red, black, even, odd, 1st12, 2nd12, 3rd12)"
    )
    @app_commands.describe(
        bet="Amount to bet",
        choice="Your bet choice"
    )
    @app_commands.choices(choice=[
        app_commands.Choice(name="Red", value="red"),
        app_commands.Choice(name="Black", value="black"),
        app_commands.Choice(name="Even", value="even"),
        app_commands.Choice(name="Odd", value="odd"),
        app_commands.Choice(name="1st 12", value="1st12"),
        app_commands.Choice(name="2nd 12", value="2nd12"),
        app_commands.Choice(name="3rd 12", value="3rd12"),
    ])
    async def roulette(self, interaction: discord.Interaction, bet: int, choice: app_commands.Choice[str]):

        await interaction.response.defer()

        if not interaction.guild:
            return await interaction.response.send_message("Guild only command.", ephemeral=True)

        settings = self.bot.settings.setdefault(str(interaction.guild.id), {})

        allowed, remaining = check_cooldown(
            interaction.guild.id,
            interaction.user.id,
            "roulette",
            settings
        )

        if not allowed:
            return await interaction.response.send_message(
                f"⏳ Wait {remaining}s before using this command again.",
                ephemeral=True
            )

        if bet <= 0:
            return await interaction.response.send_message(
                "❌ Bet must be higher than 0.",
                ephemeral=True
            )

        guild_id = interaction.guild.id
        user_id = interaction.user.id

        user = self.get_user(guild_id, user_id, interaction.user.name)

        if user["balance"] < bet:
            return await interaction.response.send_message(
                "❌ Not enough money.",
                ephemeral=True
            )

        # remove bet
        self.update_balance(guild_id, user_id, -bet)

        spin = discord.Embed(
            title="🎡 Spinning Roulette...",
            description="The wheel is spinning...",
            color=discord.Color.dark_grey()
        )

        await interaction.response.send_message(embed=spin)

        await asyncio.sleep(2)

        number = random.randint(0, 36)
        color = get_color(number)

        c = choice.value

        win = False
        multiplier = 0

        if c == "red":
            win = color == "red"
            multiplier = 2

        elif c == "black":
            win = color == "black"
            multiplier = 2

        elif c == "even":
            win = number != 0 and number % 2 == 0
            multiplier = 2

        elif c == "odd":
            win = number % 2 == 1
            multiplier = 2

        elif c == "1st12":
            win = 1 <= number <= 12
            multiplier = 3

        elif c == "2nd12":
            win = 13 <= number <= 24
            multiplier = 3

        elif c == "3rd12":
            win = 25 <= number <= 36
            multiplier = 3

        if win:
            payout = bet * multiplier
            self.update_balance(guild_id, user_id, payout)

            result_text = f"🎉 You WON! +${payout - bet}"
            color_embed = discord.Color.green()
        else:
            result_text = f"💀 You lost -${bet}"
            color_embed = discord.Color.red()

        updated = self.get_user(guild_id, user_id, interaction.user.name)

        result = discord.Embed(
            title="🎡 Roulette Result",
            color=color_embed
        )

        result.add_field(
            name="Number",
            value=f"🎯 {number} ({color})",
            inline=False
        )

        result.add_field(
            name="Your Bet",
            value=f"{choice.name} (${bet})",
            inline=True
        )

        result.add_field(
            name="Result",
            value=result_text,
            inline=False
        )

        result.add_field(
            name="🏦 Balance",
            value=f"${updated.get('balance', 0)}",
            inline=True
        )

        await interaction.edit_original_response(embed=result)


async def setup(bot):
    await bot.add_cog(Roulette(bot))