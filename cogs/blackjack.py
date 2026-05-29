import discord
from discord.ext import commands
from discord import app_commands
import random
from motor.motor_asyncio import ReturnDocument
from utils import check_cooldown


# =========================
# BLACKJACK GAME VIEW
# =========================
class BlackjackView(discord.ui.View):

    def __init__(self, cog, guild_id, user_id, bet, player_hand, dealer_hand):
        super().__init__(timeout=120)

        self.cog = cog
        self.guild_id = str(guild_id)
        self.user_id = str(user_id)
        self.bet = bet

        self.player = player_hand
        self.dealer = dealer_hand

        self.finished = False

    # -------------------------
    # CALCULATE HAND
    # -------------------------
    def calculate(self, hand):
        total = sum(hand)
        aces = hand.count(11)

        while total > 21 and aces:
            total -= 10
            aces -= 1

        return total

    # -------------------------
    # DEALER TURN
    # -------------------------
    async def dealer_play(self):
        while self.calculate(self.dealer) < 17:
            self.dealer.append(self.cog.draw_card())

    # -------------------------
    # DB UPDATE
    # -------------------------
    async def update_balance(self, amount):
        await self.cog.economy.update_one(
            {"guild_id": self.guild_id, "user_id": self.user_id},
            {"$inc": {"balance": amount}},
            upsert=True
        )

    # -------------------------
    # END GAME
    # -------------------------
    async def end_game(self, interaction, result_text, color, win_state):
        self.finished = True

        for item in self.children:
            item.disabled = True

        updated = await self.cog.get_user(self.guild_id, self.user_id, interaction.user.name)

        embed = discord.Embed(
            title="🃏 Blackjack Result",
            description=result_text,
            color=color
        )

        embed.add_field(
            name="Your Hand",
            value=f"{self.player} = {self.calculate(self.player)}",
            inline=False
        )

        embed.add_field(
            name="Dealer Hand",
            value=f"{self.dealer} = {self.calculate(self.dealer)}",
            inline=False
        )

        embed.add_field(name="Bet", value=f"${self.bet}", inline=True)
        embed.add_field(name="Balance", value=f"${updated.get('balance', 0)}", inline=True)

        await interaction.response.edit_message(embed=embed, view=self)

    # -------------------------
    # HIT BUTTON
    # -------------------------
    @discord.ui.button(label="Hit", style=discord.ButtonStyle.green)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id != int(self.user_id):
            return await interaction.response.send_message("❌ Not your game.", ephemeral=True)

        if self.finished:
            return

        self.player.append(self.cog.draw_card())

        if self.calculate(self.player) > 21:
            await self.end_game(
                interaction,
                "💀 You busted!",
                discord.Color.red(),
                False
            )
            return

        await interaction.response.edit_message(
            embed=self.cog.build_embed(self.player, self.dealer, self.bet),
            view=self
        )

    # -------------------------
    # STAND BUTTON
    # -------------------------
    @discord.ui.button(label="Stand", style=discord.ButtonStyle.gray)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id != int(self.user_id):
            return await interaction.response.send_message("❌ Not your game.", ephemeral=True)

        if self.finished:
            return

        await self.dealer_play()

        p = self.calculate(self.player)
        d = self.calculate(self.dealer)

        if d > 21 or p > d:
            await self.cog.economy.update_one(
                {"guild_id": self.guild_id, "user_id": self.user_id},
                {"$inc": {"balance": self.bet * 2}},
                upsert=True
            )
            await self.end_game(interaction, "🎉 You win!", discord.Color.green(), True)

        elif p == d:
            await self.cog.economy.update_one(
                {"guild_id": self.guild_id, "user_id": self.user_id},
                {"$inc": {"balance": self.bet}},
                upsert=True
            )
            await self.end_game(interaction, "🤝 Tie!", discord.Color.gold(), "tie")

        else:
            await self.end_game(interaction, "💀 Dealer wins!", discord.Color.red(), False)


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
            {
                "$setOnInsert": {
                    "guild_id": str(guild_id),
                    "user_id": str(user_id),
                    "balance": 0,
                    "name": name
                }
            },
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

    def draw_card(self):
        return random.choice([2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11])

    def calculate(self, hand):
        total = sum(hand)
        aces = hand.count(11)

        while total > 21 and aces:
            total -= 10
            aces -= 1

        return total

    # -------------------------
    # EMBED BUILDER
    # -------------------------
    def build_embed(self, player, dealer, bet):
        return discord.Embed(
            title="🃏 Blackjack",
            description="Hit or Stand?",
            color=discord.Color.dark_blue()
        ).add_field(
            name="Your Hand",
            value=f"{player} = {self.calculate(player)}",
            inline=False
        ).add_field(
            name="Dealer Showing",
            value=f"[{dealer[0]}, ❓]",
            inline=False
        ).add_field(
            name="Bet",
            value=f"${bet}",
            inline=True
        )

    # -------------------------
    # COMMAND
    # -------------------------
    @app_commands.command(name="blackjack", description="Play real blackjack")
    async def blackjack(self, interaction: discord.Interaction, bet: int):

        if not interaction.guild:
            return await interaction.response.send_message("❌ Must be used in a server.", ephemeral=True)

        if bet <= 0:
            return await interaction.response.send_message("❌ Bet must be higher than 0.", ephemeral=True)

        settings = self.bot.settings.setdefault(str(interaction.guild.id), {})

        allowed, remaining = check_cooldown(
            interaction.guild.id,
            interaction.user.id,
            "blackjack",
            settings
        )

        if not allowed:
            return await interaction.response.send_message(
                f"⏳ Wait {remaining}s before using this command again.",
                ephemeral=True
            )

        user = await self.get_user(interaction.guild.id, interaction.user.id, interaction.user.name)

        if user.get("balance", 0) < bet:
            return await interaction.response.send_message("❌ Not enough money.", ephemeral=True)

        await self.economy.update_one(
            {"guild_id": str(interaction.guild.id), "user_id": str(interaction.user.id)},
            {"$inc": {"balance": -bet}},
            upsert=True
        )

        player = [self.draw_card(), self.draw_card()]
        dealer = [self.draw_card(), self.draw_card()]

        view = BlackjackView(
            self,
            interaction.guild.id,
            interaction.user.id,
            bet,
            player,
            dealer
        )

        await interaction.response.send_message(
            embed=self.build_embed(player, dealer, bet),
            view=view
        )


async def setup(bot):
    await bot.add_cog(Blackjack(bot))