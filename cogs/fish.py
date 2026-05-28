import discord
from discord.ext import commands
from discord import app_commands
import random
from utils import check_cooldown
from pymongo import ReturnDocument


FISHES = ["🐟 Blue Fish", "🐠 Gold Fish", "🐡 Red Fish", "🦈 Shark", "🐙 Octo Fish"]


# =========================
# FISH GAME VIEW
# =========================
class FishRaceView(discord.ui.View):

    def __init__(self, bot, guild_id, user_id, bet):
        super().__init__(timeout=60)
        self.bot = bot
        self.guild_id = str(guild_id)
        self.user_id = str(user_id)
        self.bet = bet

        self.winner = random.choice(FISHES)
        self.finished = False

    # =========================
    # USER SYSTEM
    # =========================
    def get_user(self):
        return self.bot.economy.find_one_and_update(
            {"guild_id": self.guild_id, "user_id": self.user_id},
            {
                "$setOnInsert": {
                    "guild_id": self.guild_id,
                    "user_id": self.user_id,
                    "balance": 0
                }
            },
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

    def update_balance(self, amount):
        self.bot.economy.update_one(
            {"guild_id": self.guild_id, "user_id": self.user_id},
            {"$inc": {"balance": amount}}
        )

    # =========================
    # RESULT HANDLER
    # =========================
    async def resolve(self, interaction: discord.Interaction, choice: str):

        if self.finished:
            return

        self.finished = True

        # disable buttons immediately (prevents spam)
        for item in self.children:
            item.disabled = True

        if choice == self.winner:
            payout = self.bet * 4
            profit = payout - self.bet

            self.update_balance(profit)

            result = f"🎉 You WON! +${profit}"
            color = discord.Color.green()

        else:
            result = f"💀 You lost! Winner was {self.winner}"
            color = discord.Color.red()

        embed = discord.Embed(
            title="🐟 Fish Race Result",
            description=result,
            color=color
        )

        await interaction.response.edit_message(embed=embed, view=self)

    # =========================
    # BUTTONS
    # =========================
    @discord.ui.button(label="Blue Fish", style=discord.ButtonStyle.secondary)
    async def blue(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.resolve(interaction, "🐟 Blue Fish")

    @discord.ui.button(label="Gold Fish", style=discord.ButtonStyle.secondary)
    async def gold(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.resolve(interaction, "🐠 Gold Fish")

    @discord.ui.button(label="Red Fish", style=discord.ButtonStyle.secondary)
    async def red(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.resolve(interaction, "🐡 Red Fish")

    @discord.ui.button(label="Shark", style=discord.ButtonStyle.secondary)
    async def shark(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.resolve(interaction, "🦈 Shark")

    @discord.ui.button(label="Octo Fish", style=discord.ButtonStyle.secondary)
    async def octo(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.resolve(interaction, "🐙 Octo Fish")


# =========================
# COG
# =========================
class FishRace(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.economy = bot.economy

    @app_commands.command(name="fish_race", description="Bet on a fish race")
    async def fish_race(self, interaction: discord.Interaction, bet: int):

        if not interaction.guild:
            return await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True
            )

        settings = self.bot.settings.setdefault(str(interaction.guild.id), {})

        allowed, remaining = check_cooldown(
            interaction.guild.id,
            interaction.user.id,
            "fish_race",
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

        user = self.economy.find_one_and_update(
            {"guild_id": str(guild_id), "user_id": str(user_id)},
            {
                "$setOnInsert": {
                    "guild_id": str(guild_id),
                    "user_id": str(user_id),
                    "balance": 0
                }
            },
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

        if user.get("balance", 0) < bet:
            return await interaction.response.send_message(
                "❌ Not enough money.",
                ephemeral=True
            )

        # take bet
        self.economy.update_one(
            {"guild_id": str(guild_id), "user_id": str(user_id)},
            {"$inc": {"balance": -bet}}
        )

        view = FishRaceView(self.bot, guild_id, user_id, bet)

        embed = discord.Embed(
            title="🐟 Fish Race",
            description="Pick your fish!",
            color=discord.Color.dark_gray()
        )

        await interaction.response.send_message(embed=embed, view=view)


# =========================
# SETUP
# =========================
async def setup(bot):
    await bot.add_cog(FishRace(bot))