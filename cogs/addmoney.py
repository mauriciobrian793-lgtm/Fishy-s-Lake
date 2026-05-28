import discord
from discord.ext import commands
from discord import app_commands


class AddMoney(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.economy = bot.economy

    # -------------------------
    # GET OR CREATE USER
    # -------------------------
    def get_user(self, guild_id, user_id, name):
        return self.economy.find_one_and_update(
            {
                "guild_id": str(guild_id),
                "user_id": str(user_id)
            },
            {
                "$setOnInsert": {
                    "guild_id": str(guild_id),
                    "user_id": str(user_id),
                    "balance": 0,
                    "name": name
                }
            },
            upsert=True,
            return_document=True
        )

    # -------------------------
    # COMMAND
    # -------------------------
    @app_commands.command(
        name="addmoney",
        description="Add money to a user"
    )
    async def addmoney(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        amount: int
    ):

        # =========================
        # SETTINGS LOAD (SAFE)
        # =========================
        settings = self.bot.settings.setdefault(str(interaction.guild.id), {})

        # =========================
        # ADMIN ROLE CHECK
        # =========================
        admin_role_id = settings.get("admin_role_id")

        if admin_role_id:
            if str(admin_role_id) not in [str(r.id) for r in interaction.user.roles]:
                return await interaction.response.send_message(
                    "❌ You are not allowed to use this command.",
                    ephemeral=True
                )

        # =========================
        # VALIDATION
        # =========================
        if amount <= 0:
            return await interaction.response.send_message(
                "❌ Amount must be greater than 0.",
                ephemeral=True
            )

        # =========================
        # UPDATE USER
        # =========================
        self.economy.update_one(
            {
                "guild_id": str(interaction.guild.id),
                "user_id": str(user.id)
            },
            {
                "$inc": {"balance": amount},
                "$set": {"name": user.name}
            },
            upsert=True
        )

        # =========================
        # GET UPDATED DATA
        # =========================
        updated = self.economy.find_one({
            "guild_id": str(interaction.guild.id),
            "user_id": str(user.id)
        }) or {"balance": 0}

        # =========================
        # EMBED
        # =========================
        embed = discord.Embed(
            title="💰 Money Added",
            description=f"Gave money to {user.mention}",
            color=discord.Color.green()
        )

        embed.add_field(
            name="💵 Amount Added",
            value=f"${amount}",
            inline=True
        )

        embed.add_field(
            name="🏦 New Balance",
            value=f"${updated.get('balance', 0)}",
            inline=True
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(AddMoney(bot))