import discord
from discord.ext import commands
from discord import app_commands
import aiohttp


class Suggest(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        # PUT YOUR WEBHOOK URL HERE
        self.webhook_url = "https://discord.com/api/webhooks/1510210865423716373/sDs1VL29FQbg3XrCHguCTya3Sj2Kz_Y7IYl15vw4wME_XKxfgvzeSQ9wLyjTPttwwo85"

    @app_commands.command(
        name="suggest",
        description="Send a suggestion to the developers"
    )
    async def suggest(
        self,
        interaction: discord.Interaction,
        suggestion: str
    ):

        embed = {
            "title": "💡 New Suggestion",
            "description": suggestion,
            "color": 0x5865F2,
            "fields": [
                {
                    "name": "👤 User",
                    "value": f"{interaction.user} ({interaction.user.id})",
                    "inline": False
                },
                {
                    "name": "🏠 Server",
                    "value": (
                        f"{interaction.guild.name} ({interaction.guild.id})"
                        if interaction.guild
                        else "Direct Message"
                    ),
                    "inline": False
                }
            ]
        }

        payload = {
            "username": "Fishy Suggestions",
            "embeds": [embed]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload
                ) as response:

                    if response.status not in (200, 204):
                        raise Exception(f"Webhook returned {response.status}")

            await interaction.response.send_message(
                "✅ Suggestion sent!",
                ephemeral=True
            )

        except Exception as e:

            await interaction.response.send_message(
                f"❌ Failed to send suggestion.\n```{e}```",
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(Suggest(bot))