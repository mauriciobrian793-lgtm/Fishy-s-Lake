import discord
from discord.ext import commands
from discord import app_commands


# =========================
# ROLE INCOME MODAL
# =========================
class IncomeRoleModal(discord.ui.Modal):

    def __init__(self, role_id, bot):
        super().__init__(title="Set Role Income")
        self.role_id = str(role_id)
        self.bot = bot

        self.amount = discord.ui.TextInput(
            label="Income amount per collect",
            placeholder="Example: 500",
            required=True
        )

        self.add_item(self.amount)

    async def on_submit(self, interaction: discord.Interaction):

        try:
            amount = int(self.amount.value)
            if amount < 0:
                raise ValueError()
        except:
            return await interaction.response.send_message(
                "❌ Must be a valid number.",
                ephemeral=True
            )

        settings = self.bot.settings.setdefault(str(interaction.guild.id), {})
        role_income = settings.setdefault("role_income", {})

        role_income[str(self.role_id)] = amount

        await interaction.response.send_message(
            f"💰 Role income set: <@&{self.role_id}> → ${amount}",
            ephemeral=True
        )


# =========================
# COOLDOWN MODAL
# =========================
class CooldownModal(discord.ui.Modal):

    def __init__(self, command, bot):
        super().__init__(title=f"Cooldown: {command}")
        self.command = command
        self.bot = bot

        self.seconds = discord.ui.TextInput(
            label="Cooldown seconds",
            placeholder="Example: 60",
            required=True
        )

        self.add_item(self.seconds)

    async def on_submit(self, interaction: discord.Interaction):

        try:
            seconds = int(self.seconds.value)
            if seconds < 0:
                raise ValueError()
        except:
            return await interaction.response.send_message(
                "❌ Invalid number.",
                ephemeral=True
            )

        settings = self.bot.settings.setdefault(str(interaction.guild.id), {})
        cooldowns = settings.setdefault("cooldowns", {})

        cooldowns[self.command] = seconds

        await interaction.response.send_message(
            f"⏱ `{self.command}` cooldown set to {seconds}s",
            ephemeral=True
        )


# =========================
# COMMAND SELECT
# =========================
class CommandSelect(discord.ui.Select):

    def __init__(self):
        options = [
            discord.SelectOption(label="work"),
            discord.SelectOption(label="crime"),
            discord.SelectOption(label="rob"),
            discord.SelectOption(label="roulette"),
            discord.SelectOption(label="fish_race"),
            discord.SelectOption(label="blackjack"),
            discord.SelectOption(label="collect_income"),
        ]

        super().__init__(
            placeholder="Select command cooldown",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            CooldownModal(self.values[0], interaction.client)
        )


class CommandView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(CommandSelect())


# =========================
# ROLE SELECT
# =========================
class RoleSelect(discord.ui.Select):

    def __init__(self, roles):
        roles = roles[:25]  # hard safety cap

        options = [
            discord.SelectOption(label=r.name[:100], value=str(r.id))
            for r in roles
        ]

        super().__init__(
            placeholder="Select role",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            IncomeRoleModal(self.values[0], interaction.client)
        )


class RoleView(discord.ui.View):
    def __init__(self, roles):
        super().__init__(timeout=60)
        self.add_item(RoleSelect(roles))


# =========================
# DASHBOARD COG
# =========================
class Dashboard(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="dashboard",
        description="Economy control panel"
    )
    async def dashboard(self, interaction: discord.Interaction):

        if not interaction.guild:
            return await interaction.response.send_message(
                "❌ Server only command.",
                ephemeral=True
            )

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "❌ Admin only.",
                ephemeral=True
            )

        guild_id = str(interaction.guild.id)
        settings = self.bot.settings.setdefault(guild_id, {})

        admin_role = settings.get("admin_role_id")
        cooldowns = settings.get("cooldowns", {})
        role_income = settings.get("role_income", {})

        embed = discord.Embed(
            title="⚙️ Economy Dashboard",
            color=discord.Color.dark_grey()
        )

        embed.add_field(
            name="Admin Role",
            value=f"<@&{admin_role}>" if admin_role else "Not set",
            inline=False
        )

        embed.add_field(
            name="Cooldowns",
            value=str(cooldowns) if cooldowns else "None",
            inline=False
        )

        income_text = "\n".join(
            [f"<@&{r}> → ${a}" for r, a in role_income.items()]
        ) or "None set"

        embed.add_field(
            name="💼 Income Roles",
            value=income_text,
            inline=False
        )

        # =========================
        # MAIN VIEW
        # =========================
        class MainView(discord.ui.View):

            @discord.ui.button(label="Set Admin Role", style=discord.ButtonStyle.secondary)
            async def admin(self, interaction2: discord.Interaction, button: discord.ui.Button):

                if not interaction2.user.guild_permissions.administrator:
                    return await interaction2.response.send_message("❌ Admin only", ephemeral=True)

                await interaction2.response.send_message(
                    "Select admin role:",
                    view=RoleView(interaction.guild.roles),
                    ephemeral=True
                )

            @discord.ui.button(label="Set Cooldown", style=discord.ButtonStyle.secondary)
            async def cooldown(self, interaction2: discord.Interaction, button: discord.ui.Button):

                if not interaction2.user.guild_permissions.administrator:
                    return await interaction2.response.send_message("❌ Admin only", ephemeral=True)

                await interaction2.response.send_message(
                    "Pick command:",
                    view=CommandView(),
                    ephemeral=True
                )

            @discord.ui.button(label="Set Income Role", style=discord.ButtonStyle.secondary)
            async def income(self, interaction2: discord.Interaction, button: discord.ui.Button):

                if not interaction2.user.guild_permissions.administrator:
                    return await interaction2.response.send_message("❌ Admin only", ephemeral=True)

                await interaction2.response.send_message(
                    "Pick a role:",
                    view=RoleView(interaction.guild.roles),
                    ephemeral=True
                )

        await interaction.response.send_message(embed=embed, view=MainView())


async def setup(bot):
    await bot.add_cog(Dashboard(bot))