import discord
from discord.ext import commands
from discord import app_commands
import random
from motor.motor_asyncio import ReturnDocument
from utils import check_cooldown


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

    @app_commands.command(
        name="blackjack",
        description="Play blackjack against the dealer"
    )
    async def blackjack(self, interaction: discord.Interaction, bet: int):

        if not interaction.guild:
            return await interaction.response.send_message(
                "❌ Must be used in a server.",
                ephemeral=True
            )

        if bet <= 0:
            return await interaction.response.send_message(
                "❌ Bet must be higher than 0.",
                ephemeral=True
            )

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

        guild_id = interaction.guild.id
        user_id = interaction.user.id

        user = await self.get_user(guild_id, user_id, interaction.user.name)

        if user.get("balance", 0) < bet:
            return await interaction.response.send_message(
                "❌ Not enough money.",
                ephemeral=True
            )

        await interaction.response.defer()

        await self.economy.update_one(
            {"guild_id": str(guild_id), "user_id": str(user_id)},
            {"$inc": {"balance": -bet}},
            upsert=True
        )

        # GAME
        player = [self.draw_card(), self.draw_card()]
        dealer = [self.draw_card(), self.draw_card()]

        while self.calculate(player) < 17:
            player.append(self.draw_card())

        while self.calculate(dealer) < 17:
            dealer.append(self.draw_card())

        player_total = self.calculate(player)
        dealer_total = self.calculate(dealer)

        if player_total > 21:
            result = "💀 You busted!"
            win = False

        elif dealer_total > 21 or player_total > dealer_total:
            result = "🎉 You win!"
            win = True

        elif player_total == dealer_total:
            result = "🤝 Tie!"
            win = "tie"

        else:
            result = "💀 Dealer wins!"
            win = False

        # PAYOUT
        if win is True:
            await self.economy.update_one(
                {"guild_id": str(guild_id), "user_id": str(user_id)},
                {"$inc": {"balance": bet * 2}},
                upsert=True
            )

        elif win == "tie":
            await self.economy.update_one(
                {"guild_id": str(guild_id), "user_id": str(user_id)},
                {"$inc": {"balance": bet}},
                upsert=True
            )

        updated = await self.get_user(guild_id, user_id, interaction.user.name)

        color = (
            discord.Color.green() if win is True else
            discord.Color.gold() if win == "tie" else
            discord.Color.red()
        )

        embed = discord.Embed(
            title="🃏 Blackjack",
            description=result,
            color=color
        )

        embed.add_field(name="Your Hand", value=f"{player} = {player_total}", inline=False)
        embed.add_field(name="Dealer Hand", value=f"{dealer} = {dealer_total}", inline=False)
        embed.add_field(name="Bet", value=f"${bet}", inline=True)
        embed.add_field(name="Balance", value=f"${updated.get('balance', 0)}", inline=True)

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Blackjack(bot))