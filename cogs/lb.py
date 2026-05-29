import discord
from discord.ext import commands
from discord import app_commands
import math
from utils import check_cooldown


# =========================
# LEADERBOARD VIEW
# =========================
class LeaderboardView(discord.ui.View):

    def __init__(self, users):
        super().__init__(timeout=120)
        self.users = users
        self.page = 0
        self.per_page = 10

    def create_embed(self):

        total_pages = max(1, math.ceil(len(self.users) / self.per_page))

        self.page = max(0, min(self.page, total_pages - 1))

        start = self.page * self.per_page
        end = start + self.per_page
        current = self.users[start:end]

        embed = discord.Embed(
            title="🏆 Economy Leaderboard",
            color=discord.Color.gold()
        )

        if not current:
            embed.description = "No users found."
            return embed

        text = ""
        for i, doc in enumerate(current, start=start + 1):
            name = doc.get("name", "Unknown User")
            balance = doc.get("balance", 0)
            text += f"**#{i}** • {name} — `${balance}`\n"

        embed.description = text
        embed.set_footer(text=f"Page {self.page + 1}/{total_pages}")

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

        total_pages = max(1, math.ceil(len(self.users) / self.per_page))

        if self.page < total_pages - 1:
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
        self.economy = bot.economy

    @app_commands.command(
        name="leaderboard",
        description="View richest users"
    )
    async def leaderboard(self, interaction: discord.Interaction):

        await interaction.response.defer()  # ✅ FIX: prevents timeout

        if not interaction.guild:
            return await interaction.followup.send(
                "❌ This command can only be used in a server.",
                ephemeral=True
            )

        settings = self.bot.settings.setdefault(str(interaction.guild.id), {})

        allowed, remaining = check_cooldown(
            interaction.guild.id,
            interaction.user.id,
            "leaderboard",
            settings
        )

        if not allowed:
            return await interaction.followup.send(
                f"⏳ Wait {remaining}s before using this command again.",
                ephemeral=True
            )

        guild_id = str(interaction.guild.id)

        # (Motor async query - correct)
        users = await self.economy.find(
            {"guild_id": guild_id}
        ).to_list(length=1000)  # ✅ prevents huge lag

        if not users:
            return await interaction.followup.send(
                "❌ No data yet in this server.",
                ephemeral=True
            )

        users = sorted(
            users,
            key=lambda x: x.get("balance", 0),
            reverse=True
        )

        view = LeaderboardView(users)

        await interaction.followup.send(
            embed=view.create_embed(),
            view=view
        )


async def setup(bot):
    await bot.add_cog(Leaderboard(bot))