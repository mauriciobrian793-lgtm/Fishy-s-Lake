import discord
from discord.ext import commands
from discord import app_commands
import random
from motor.motor_asyncio import ReturnDocument
from utils import check_cooldown


# =========================
# EMBED BUILDER (V2 STYLE)
# =========================
def embed(title, desc=None, color=discord.Color.blurple()):
    e = discord.Embed(
        title=title,
        description=desc,
        color=color,
        timestamp=discord.utils.utcnow()
    )
    e.set_footer(text="Blackjack V3 • Casino System")
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
        self.bet2 = 0  # for split

        self.hands = [[cog.draw_card(), cog.draw_card()]]
        self.dealer = [cog.draw_card(), cog.draw_card()]

        self.active_hand = 0
        self.finished = False
        self.doubled = False

    # =========================
    # CALC
    # =========================
    def calc(self, hand):
        total = sum(hand)
        aces = hand.count(11)

        while total > 21 and aces:
            total -= 10
            aces -= 1

        return total

    # =========================
    # DEALER
    # =========================
    async def dealer_play(self):
        while self.calc(self.dealer) < 17:
            self.dealer.append(self.cog.draw_card())

    # =========================
    # WIN STREAK UPDATE
    # =========================
    async def update_streak(self, win: bool):
        data = await self.cog.get_user(self.guild_id, self.user_id, "user")

        streak = data.get("win_streak", 0)

        if win:
            streak += 1
        else:
            streak = 0

        await self.cog.economy.update_one(
            {"guild_id": self.guild_id, "user_id": self.user_id},
            {"$set": {"win_streak": streak}},
            upsert=True
        )

    # =========================
    # END GAME
    # =========================
    async def finish(self, interaction, result, color, win_state):
        self.finished = True

        for b in self.children:
            b.disabled = True

        await self.update_streak(win_state is True)

        data = await self.cog.get_user(self.guild_id, self.user_id, interaction.user.name)

        e = embed("🃏 Blackjack Result", result, color)

        e.add_field(
            name="🧠 Final Hand",
            value=f"{self.hands} = **{self.calc(self.hands[self.active_hand])}**",
            inline=False
        )

        e.add_field(
            name="🎴 Dealer",
            value=f"{self.dealer} = **{self.calc(self.dealer)}**",
            inline=False
        )

        e.add_field(name="💰 Bet", value=f"${self.bet}", inline=True)
        e.add_field(name="🔥 Win Streak", value=str(data.get("win_streak", 0)), inline=True)
        e.add_field(name="🏦 Balance", value=f"${data.get('balance', 0)}", inline=True)

        await interaction.response.edit_message(embed=e, view=self)

    # =========================
    # HIT
    # =========================
    @discord.ui.button(label="Hit", style=discord.ButtonStyle.green)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id != int(self.user_id):
            return await interaction.response.send_message("❌ Not your game.", ephemeral=True)

        hand = self.hands[self.active_hand]
        hand.append(self.cog.draw_card())

        if self.calc(hand) > 21:
            await self.finish(interaction, "💀 You busted!", discord.Color.red(), False)
            return

        e = embed("🃏 Blackjack", "Hit or Stand", discord.Color.blurple())
        e.add_field(name="Hand", value=str(self.hands), inline=False)
        e.add_field(name="Dealer", value=f"[{self.dealer[0]}, ❓]", inline=False)

        await interaction.response.edit_message(embed=e, view=self)

    # =========================
    # STAND
    # =========================
    @discord.ui.button(label="Stand", style=discord.ButtonStyle.gray)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id != int(self.user_id):
            return await interaction.response.send_message("❌ Not your game.", ephemeral=True)

        await self.dealer_play()

        p = self.calc(self.hands[0])
        d = self.calc(self.dealer)

        # payout
        if d > 21 or p > d:
            await self.cog.economy.update_one(
                {"guild_id": self.guild_id, "user_id": self.user_id},
                {"$inc": {"balance": self.bet * 2}},
                upsert=True
            )
            await self.finish(interaction, "🎉 You win!", discord.Color.green(), True)

        elif p == d:
            await self.cog.economy.update_one(
                {"guild_id": self.guild_id, "user_id": self.user_id},
                {"$inc": {"balance": self.bet}},
                upsert=True
            )
            await self.finish(interaction, "🤝 Tie!", discord.Color.gold(), True)

        else:
            await self.finish(interaction, "💀 Dealer wins!", discord.Color.red(), False)

    # =========================
    # DOUBLE DOWN
    # =========================
    @discord.ui.button(label="Double", style=discord.ButtonStyle.blurple)
    async def double(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id != int(self.user_id):
            return await interaction.response.send_message("❌ Not your game.", ephemeral=True)

        self.bet *= 2
        self.hands[0].append(self.cog.draw_card())

        await self.stand(interaction, button)

    # =========================
    # SPLIT
    # =========================
    @discord.ui.button(label="Split", style=discord.ButtonStyle.red)
    async def split(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id != int(self.user_id):
            return await interaction.response.send_message("❌ Not your game.", ephemeral=True)

        if len(self.hands[0]) != 2 or self.hands[0][0] != self.hands[0][1]:
            return await interaction.response.send_message("❌ Can't split.", ephemeral=True)

        self.hands = [
            [self.hands[0][0], self.cog.draw_card()],
            [self.hands[0][1], self.cog.draw_card()]
        ]

        await interaction.response.edit_message(
            embed=embed("🃏 Split Hand", "Playing 2 hands", discord.Color.orange()),
            view=self
        )


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
            {"$setOnInsert": {"balance": 0, "win_streak": 0, "name": name}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

    def draw_card(self):
        return random.choice([2,3,4,5,6,7,8,9,10,10,10,10,11])

    # =========================
    # COMMAND (FIXED + WORKING)
    # =========================
    @app_commands.command(name="blackjack", description="Play Blackjack V3")
    async def blackjack(self, interaction: discord.Interaction, bet: int):

        if not interaction.guild:
            return await interaction.response.send_message("Server only.", ephemeral=True)

        if bet <= 0:
            return await interaction.response.send_message("Invalid bet.", ephemeral=True)

        settings = self.bot.settings.setdefault(str(interaction.guild.id), {})

        allowed, remaining = check_cooldown(
            interaction.guild.id,
            interaction.user.id,
            "blackjack",
            settings
        )

        if not allowed:
            return await interaction.response.send_message(
                f"Cooldown: {remaining}s",
                ephemeral=True
            )

        user = await self.get_user(interaction.guild.id, interaction.user.id, interaction.user.name)

        if user.get("balance", 0) < bet:
            return await interaction.response.send_message("Not enough money.", ephemeral=True)

        await self.economy.update_one(
            {"guild_id": str(interaction.guild.id), "user_id": str(interaction.user.id)},
            {"$inc": {"balance": -bet}},
            upsert=True
        )

        view = BlackjackView(self, interaction.guild.id, interaction.user.id, bet)

        await interaction.response.send_message(
            embed=embed("🃏 Blackjack V3", "Hit, Stand, Split or Double"),
            view=view
        )


async def setup(bot):
    await bot.add_cog(Blackjack(bot))