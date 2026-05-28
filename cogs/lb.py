import discord
from discord.ext import commands
from discord import app_commands
import math
from utils import check_cooldown


# =========================
# LEADERBOARD VIEW
# =========================
class LeaderboardView(discord.ui.View):

    def __init__(self, users, page=0):
        super().__init__(timeout=120)
        self.users = users
        self.page = page
        self.per_page = 10

    def create_embed(self):

        start = self.page * self.per_page
        end = start + self.per_page
        current = self.users[start:end]

        embed = discord.Embed(
            title="🏆 Economy Leaderboard",
            color=discord.Color.gold()
        )

        text = ""

        for i, doc in enumerate(current, start=start + 1):
            name = doc.get("name", "Unknown User")
            balance = doc.get("balance", 0)
            text += f"**#{i}** • {name} — `${balance}`\n"

        if not text:
            text = "No users found."

        pages = max(1, math.ceil(len(self.users) / self.per_page))

        embed.description = text
        embed.set_footer(text=f"Page {self.page + 1}/{pages}")

        return embed

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.gray)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.page > 0:
            self.page -= 1

        await interaction.response.edit_message(
            embed=self.create_embed(),
            view=self
        )

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.gray)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):

        max_page = max(0, math.ceil(len(self.users) / self.per_page) - 1)

        if self.page < max_page:
            self.page += 1

        await interaction.response.edit_message(
            embed=self.create_embed(),
            view=self
        )


# =========================
# COG
# =========================
class Leaderboard(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.economy = bot.economy  # MongoDB collection

    @app_commands.command(
        name="leaderboard",
        description="View richest users"
    )
    async def leaderboard(self, interaction: discord.Interaction):

        settings = self.bot.settings.setdefault(str(interaction.guild.id), {})

        # =========================
        # COOLDOWN CHECK (FIXED)
        # =========================
        allowed, remaining = check_cooldown(
            interaction.guild.id,
            interaction.user.id,
            "leaderboard",
            settings
        )

        if not allowed:
            return await interaction.response.send_message(
                f"⏳ Wait {remaining}s before using this command again.",
                ephemeral=True
            )

        guild_id = str(interaction.guild.id)

        # =========================
        # GET USERS
        # =========================
        users = list(self.economy.find({"guild_id": guild_id}))

        if not users:
            return await interaction.response.send_message(
                "❌ No data yet in this server.",
                ephemeral=True
            )

        # =========================
        # SORT BY BALANCE
        # =========================
        users = sorted(
            users,
            key=lambda x: x.get("balance", 0),
            reverse=True
        )

        view = LeaderboardView(users)

        await interaction.response.send_message(
            embed=view.create_embed(),
            view=view
        )


# =========================
# SETUP
# =========================
async def setup(bot):
    await bot.add_cog(Leaderboard(bot))