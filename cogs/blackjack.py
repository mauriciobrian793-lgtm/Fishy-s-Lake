import discord
from discord.ext import commands
from discord import app_commands
import random
from pymongo import ReturnDocument
from utils import check_cooldown, get_settings


# =========================
# CARD SYSTEM (REAL UNICODE)
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

UNICODE = {
    "A♠":"🂡","A♥":"🂱","A♦":"🃁","A♣":"🃑",
    "2♠":"🂢","2♥":"🂲","2♦":"🃂","2♣":"🃒",
    "3♠":"🂣","3♥":"🂳","3♦":"🃃","3♣":"🃓",
    "4♠":"🂤","4♥":"🂴","4♦":"🃄","4♣":"🃔",
    "5♠":"🂥","5♥":"🂵","5♦":"🃅","5♣":"🃕",
    "6♠":"🂦","6♥":"🂶","6♦":"🃆","6♣":"🃖",
    "7♠":"🂧","7♥":"🂷","7♦":"🃇","7♣":"🃗",
    "8♠":"🂨","8♥":"🂸","8♦":"🃈","8♣":"🃘",
    "9♠":"🂩","9♥":"🂹","9♦":"🃉","9♣":"🃙",
    "10♠":"🂪","10♥":"🂺","10♦":"🃊","10♣":"🃚",
    "J♠":"🂫","J♥":"🂻","J♦":"🃋","J♣":"🃛",
    "Q♠":"🂭","Q♥":"🂽","Q♦":"🃍","Q♣":"🃝",
    "K♠":"🂮","K♥":"🂾","K♦":"🃎","K♣":"🃞",
    "BACK":"🂠"
}


def draw_card():
    v, val = random.choice(VALUES)
    s = random.choice(SUITS)
    return {"raw": f"{v}{s}", "value": val}


def hand_value(hand):
    total = sum(c["value"] for c in hand)
    aces = sum(1 for c in hand if c["value"] == 11)

    while total > 21 and aces:
        total -= 10
        aces -= 1

    return total


def render(hand, hide_first=False):
    out = []
    for i, c in enumerate(hand):
        if hide_first and i == 0:
            out.append(UNICODE["BACK"])
        else:
            out.append(UNICODE.get(c["raw"], "🂠"))
    return " ".join(out)


def embed(title, desc=None, color=discord.Color.blurple()):
    e = discord.Embed(
        title=title,
        description=desc,
        color=color
    )
    e.set_footer(text="Blackjack • Casino System")
    return e


# =========================
# GAME VIEW
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

    # =========================
    # DEALER AI (REAL RULES)
    # =========================
    async def dealer_play(self):
        while hand_value(self.dealer) < 17:
            self.dealer.append(draw_card())

    # =========================
    # END GAME
    # =========================
    async def end(self, interaction, text, color, win_state):
        self.finished = True
        for item in self.children:
            item.disabled = True

        # payout
        if win_state is True:
            await self.cog.economy.update_one(
                {"guild_id": self.guild_id, "user_id": self.user_id},
                {"$inc": {"balance": self.bet * 2}},
                upsert=True
            )
        elif win_state == "tie":
            await self.cog.economy.update_one(
                {"guild_id": self.guild_id, "user_id": self.user_id},
                {"$inc": {"balance": self.bet}},
                upsert=True
            )

        user = await self.cog.get_user(self.guild_id, self.user_id, interaction.user.name)

        e = embed("🃏 Blackjack", text, color)

        e.add_field(name="Your Hand", value=f"{render(self.player)}\n**{hand_value(self.player)}**", inline=False)
        e.add_field(name="Dealer Hand", value=f"{render(self.dealer)}\n**{hand_value(self.dealer)}**", inline=False)
        e.add_field(name="Bet", value=f"${self.bet}", inline=True)
        e.add_field(name="Balance", value=f"${user.get('balance',0)}", inline=True)

        await interaction.response.edit_message(embed=e, view=self)

    # =========================
    # HIT
    # =========================
    @discord.ui.button(label="Hit", style=discord.ButtonStyle.gray)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id != int(self.user_id):
            return await interaction.response.send_message("❌ Not your game.", ephemeral=True)

        self.player.append(draw_card())

        if hand_value(self.player) > 21:
            await self.end(interaction, "💀 You busted!", discord.Color.red(), False)
            return

        e = embed("🃏 Blackjack", "Hit or Stand")
        e.add_field(name="Your Hand", value=render(self.player), inline=False)
        e.add_field(name="Dealer", value=render(self.dealer, hide_first=True), inline=False)

        await interaction.response.edit_message(embed=e, view=self)

    # =========================
    # STAND
    # =========================
    @discord.ui.button(label="Stand", style=discord.ButtonStyle.gray)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id != int(self.user_id):
            return await interaction.response.send_message("❌ Not your game.", ephemeral=True)

        await self.dealer_play()

        p = hand_value(self.player)
        d = hand_value(self.dealer)

        if d > 21 or p > d:
            await self.end(interaction, "🎉 You win!", discord.Color.green(), True)

        elif p == d:
            await self.end(interaction, "🤝 Tie!", discord.Color.gold(), "tie")

        else:
            await self.end(interaction, "💀 Dealer wins!", discord.Color.red(), False)


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
            return_document=ReturnDocument.AFTER
        )

    # =========================
    # COMMAND
    # =========================
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
            return await interaction.response.send_message(f"Cooldown: {remaining}s", ephemeral=True)

        user = await self.get_user(interaction.guild.id, interaction.user.id, interaction.user.name)

        if user.get("balance", 0) < bet:
            return await interaction.response.send_message("Not enough money.", ephemeral=True)

        await self.economy.update_one(
            {"guild_id": str(interaction.guild.id), "user_id": str(interaction.user.id)},
            {"$inc": {"balance": -bet}},
            upsert=True
        )

        view = BlackjackView(self, interaction.guild.id, interaction.user.id, bet)

        e = embed("🃏 Blackjack", "Hit or Stand")
        e.add_field(name="Your Hand", value=render(view.player), inline=False)
        e.add_field(name="Dealer", value=render(view.dealer, hide_first=True), inline=False)

        await interaction.response.send_message(embed=e, view=view)


async def setup(bot):
    await bot.add_cog(Blackjack(bot))