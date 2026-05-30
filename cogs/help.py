import discord
from discord.ext import commands
from discord import app_commands


class Help(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="View the help menu")
    async def help(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="Command & Feature Guide",
            description="Welcome to the help menu! All available commands are listed below:",
            color=discord.Color(int("2F3136", 16))
        )

        embed.add_field(name="💰 Economy Commands", value=(
            "`/collect_income` - Collect money from your job roles\n"
            "`/balance` - Check your current balance\n"
            "`/leaderboard` - View the economy leaderboard\n"
            "`/give` - Give money to another user\n"
            "`/rob` - Attempt to rob another user\n"
            "`/work` - Work to earn money\n"
            "`/fish` - Go fishing to earn money\n"
            "`/fish_race` - Bet on a fish race\n"
            "`/roulette` - Play roulette to win money\n"
            "`/blackjack` - Play blackjack to win money\n"
            "`/equip` - Equip an item\n"
            "`/inventory` - View your owned items\n"
            "`/shop` - View the server shop\n"
            "`/withdraw` - Withdraw money from your bank\n"
            "`/deposit` - Deposit money into your bank\n"
            "`/help` - View this help menu\n"
            "More commands may be added in the future!"
        ), inline=False)

        embed.add_field(name="⚙️ Admin Commands", value=(
            "`/dashboard` - Access the economy dashboard\n"
            "`/reset_economy` - Permanently reset all economy data\n"
            "`/add_money` - Add money to a user's balance\n"
        ), inline=False)

        embed.set_image(url="https://media.discordapp.net/attachments/1508599193072304171/1510192909151109230/ChatGPT_Image_May_30_2026_01_07_04_AM.png")

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Help(bot))