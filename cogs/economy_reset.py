import discord
from discord.ext import commands
from discord import app_commands


# =========================
# CONFIRMATION VIEW
# =========================
class ResetConfirmView(discord.ui.View):

    def __init__(self, economy, guild_id):
        super().__init__(timeout=30)
        self.economy = economy
        self.guild_id = guild_id

    @discord.ui.button(label="CONFIRM RESET", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "❌ Admin only.",
                ephemeral=True
            )

        # ACTUAL DATABASE WIPE
        result = await self.economy.delete_many(
            {"guild_id": str(self.guild_id)}
        )

        embed = discord.Embed(
            title="💥 ECONOMY RESET COMPLETE",
            description="All economy data has been permanently deleted.",
            color=discord.Color.red()
        )

        embed.add_field(
            name="🗑️ Users Deleted",
            value=str(result.deleted_count),
            inline=True
        )

        await interaction.response.edit_message(embed=embed, view=None)

        self.stop()

    @discord.ui.button(label="CANCEL", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "❌ Admin only.",
                ephemeral=True
            )

        await interaction.response.edit_message(
            content="❌ Reset cancelled.",
            embed=None,
            view=None
        )

        self.stop()


# =========================
# COG
# =========================
class ResetEconomy(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.economy = bot.economy

    @app_commands.command(
        name="reset_economy",
        description="⚠️ Permanently reset ALL economy data (Admin only)"
    )
    async def reset_economy(self, interaction: discord.Interaction):

        if not interaction.guild:
            return await interaction.response.send_message(
                "❌ Server only command.",
                ephemeral=True
            )

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "❌ Admin only command.",
                ephemeral=True
            )

        guild_id = str(interaction.guild.id)

        embed = discord.Embed(
            title="⚠️ WARNING: ECONOMY RESET",
            description=(
                "This will permanently delete ALL economy data in this server.\n\n"
                "**This cannot be undone.**"
            ),
            color=discord.Color.orange()
        )

        embed.add_field(
            name="Server",
            value=interaction.guild.name,
            inline=False
        )

        embed.add_field(
            name="Action Required",
            value="Click CONFIRM RESET to proceed.",
            inline=False
        )

        view = ResetConfirmView(self.economy, guild_id)

        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(ResetEconomy(bot))