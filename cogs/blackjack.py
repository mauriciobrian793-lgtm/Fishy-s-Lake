import discord
from discord.ext import commands
from discord import app_commands
import random
from utils import check_cooldown, get_settings


# =========================
# CARDS (REAL DISPLAY)
# =========================
SUITS = ["♠", "♥", "♦", "♣"]
VALUES = [
    ("A", 11),
    ("2", 2),
    ("3", 3),
    ("4", 4),
    ("5", 5),
    ("6", 6),
    ("7", 7),
    ("8", 8),
    ("9", 9),
    ("10", 10),
    ("J", 10),
    ("Q", 10),
    ("K", 10),
]


def draw_card():
    v, val = random.choice(VALUES)
    suit = random.choice(SUITS)
    return {"name": f"{v}{suit}", "value": val}


def hand_value(hand):
    total = sum(c["value"] for c in hand)
    aces = sum(1 for c in hand if c["value"] == 11)

    while total > 21 and aces:
        total -= 10
        aces -= 1

    return total


def format_hand(hand, hide_first=False):
    if hide_first:
        return "🂠, " + ", ".join(c["name"] for c in hand[1:])
    return ", ".join(c["name"] for c in hand)


def make_embed(title, desc, color):
    e = discord.Embed(
        title=title,
        description=desc,
        color=color,
        timestamp=discord.utils.utcnow()
    )
    e.set_footer(text="Casino Blackjack")
    return e


# =========================
# VIEW (GAME)
# =========================
class BlackjackView(discord.ui.View):

    def __init__(self, cog, guild_id, user_id, bet):
        super().__init__(timeout=180)

        self.cog = cog
        self.guild_id = str(guild_id)
        self.user_id = str(user_id)

        self.bet = bet

        self.player = [draw_card(), draw_card()]
        self.dealer = [draw_card(), draw_card()]

        self.finished = False

    # -------------------------
    def dealer_play(self):
        while hand_value(self.dealer) < 17:
            self.dealer.append(draw_card())

    def end(self, interaction, result, color, payout=0):
        self.finished = True

        for b in self.children:
            b.disabled = True

        if payout != 0:
            self.cog.economy.update_one(
                {"guild_id": self.guild_id, "user_id": self.user_id},
                {"$inc": {"balance": payout}},
                upsert=True
            )

        embed = make_embed("🃏 Blackjack Result", result, color)

        embed.add_field(
            name="Your Hand",
            value=f"{format_hand(self.player)} ({hand_value(self.player)})",
            inline=False
        )

        embed.add_field(
            name="Dealer Hand",
            value=f"{format_hand(self.dealer)} ({hand_value(self.dealer)})",
            inline=False
        )

        self.cog.get_user(self.guild_id, self.user_id, "user")

        interaction.response.edit_message(embed=embed, view=self)

    # -------------------------
    @discord.ui.button(label="Hit", style=discord.ButtonStyle.secondary)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id != int(self.user_id):
            return await interaction.response.send_message("Not your game.", ephemeral=True)

        self.player.append(draw_card())

        if hand_value(self.player) > 21:
            return self.end(interaction, "💀 Bust!", discord.Color.red(), 0)

        embed = make_embed(
            "🃏 Blackjack",
            "Hit or Stand",
            discord.Color.dark_gray()
        )

        embed.add_field(
            name="Your Hand",
            value=f"{format_hand(self.player)} ({hand_value(self.player)})",
            inline=False
        )

        embed.add_field(
            name="Dealer",
            value=f"{self.dealer[0]['name']}, 🂠",
            inline=False
        )

        await interaction.response.edit_message(embed=embed, view=self)

    # -------------------------
    @discord.ui.button(label="Stand", style=discord.ButtonStyle.secondary)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id != int(self.user_id):
            return await interaction.response.send_message("Not your game.", ephemeral=True)

        self.dealer_play()

        p = hand_value(self.player)
        d = hand_value(self.dealer)

        if d > 21 or p > d:
            return self.end(interaction, "🎉 You win!", discord.Color.green(), self.bet * 2)

        if p == d:
            return self.end(interaction, "🤝 Push!", discord.Color.gold(), self.bet)

        return self.end(interaction, "💀 Dealer wins!", discord.Color.red(), 0)

    # -------------------------
    @discord.ui.button(label="Double", style=discord.ButtonStyle.secondary)
    async def double(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id != int(self.user_id):
            return await interaction.response.send_message("Not your game.", ephemeral=True)

        self.bet *= 2
        self.player.append(draw_card())

        if hand_value(self.player) > 21:
            return self.end(interaction, "💀 Bust!", discord.Color.red(), 0)

        self.stand.callback(self, interaction)


# =========================
# COG
# =========================
class Blackjack(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.economy = bot.economy

    async def get_user(self, guild_id, user_id, name):
        return await self.economy.find_one_and_update(
            {"guild_id": str(guild_id), "user_id": str(user_id)},
            {"$setOnInsert": {"balance": 0, "name": name}},
            upsert=True,
            return_document=True
        )

    @app_commands.command(name="blackjack", description="Play Blackjack")
    async def blackjack(self, interaction: discord.Interaction, bet: int):

        if bet <= 0:
            return await interaction.response.send_message("Invalid bet.", ephemeral=True)

        settings = await get_settings(self.bot, interaction.guild.id)

        allowed, remaining = check_cooldown(
            interaction.guild.id,
            interaction.user.id,
            "blackjack",
            settings
        )

        if not allowed:
            return await interaction.response.send_message(f"Cooldown {remaining}s", ephemeral=True)

        user = await self.get_user(interaction.guild.id, interaction.user.id, interaction.user.name)

        if user.get("balance", 0) < bet:
            return await interaction.response.send_message("Not enough money.", ephemeral=True)

        await self.economy.update_one(
            {"guild_id": str(interaction.guild.id), "user_id": str(interaction.user.id)},
            {"$inc": {"balance": -bet}},
            upsert=True
        )

        view = BlackjackView(self, interaction.guild.id, interaction.user.id, bet)

        embed = make_embed(
            "🃏 Blackjack",
            "Hit or Stand",
            discord.Color.dark_gray()
        )

        embed.add_field(
            name="Your Hand",
            value=f"{format_hand(view.player)} ({hand_value(view.player)})",
            inline=False
        )

        embed.add_field(
            name="Dealer",
            value=f"{view.dealer[0]['name']}, 🂠",
            inline=False
        )

        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Blackjack(bot))