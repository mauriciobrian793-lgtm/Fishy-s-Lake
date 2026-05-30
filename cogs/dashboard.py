import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput
from utils import get_settings


# =========================
# SAVE SETTINGS HELPER
# =========================
async def save_settings(bot, guild_id, settings):
    await bot.settings_db.update_one(
        {"guild_id": str(guild_id)},
        {"$set": settings},
        upsert=True
    )


# =========================
# MODALS
# =========================
class IncomeRoleModal(discord.ui.Modal):

    def __init__(self, role_id, bot):
        super().__init__(title="💼 Set Role Income")
        self.role_id = str(role_id)
        self.bot = bot

        self.amount = discord.ui.TextInput(
            label="Income amount per collect",
            placeholder="Example: 500"
        )

        self.add_item(self.amount)

    async def on_submit(self, interaction: discord.Interaction):
        settings = await get_settings(self.bot, interaction.guild.id)

        try:
            amount = int(self.amount.value)
        except:
            return await interaction.response.send_message("❌ Invalid number.", ephemeral=True)

        settings.setdefault("role_income", {})[self.role_id] = amount

        await save_settings(self.bot, interaction.guild.id, settings)

        await interaction.response.send_message(
            f"💰 Saved: <@&{self.role_id}> → `${amount}`",
            ephemeral=True
        )


class CooldownModal(discord.ui.Modal):

    def __init__(self, command, bot):
        super().__init__(title=f"⏱ Cooldown: {command}")
        self.command = command
        self.bot = bot

        self.seconds = discord.ui.TextInput(
            label="Seconds",
            placeholder="60"
        )

        self.add_item(self.seconds)

    async def on_submit(self, interaction: discord.Interaction):
        settings = await get_settings(self.bot, interaction.guild.id)

        try:
            seconds = int(self.seconds.value)
        except:
            return await interaction.response.send_message("❌ Invalid number.", ephemeral=True)

        settings.setdefault("cooldowns", {})[self.command] = seconds

        await save_settings(self.bot, interaction.guild.id, settings)

        await interaction.response.send_message(
            f"⏱ Saved `{self.command}` → `{seconds}s`",
            ephemeral=True
        )


# =========================
# SHOP MODAL
# =========================
class ShopItemModal(discord.ui.Modal, title="🛒 Add Shop Item"):

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

        self.item_name = TextInput(label="Item Name")
        self.price = TextInput(label="Price")
        self.role_id = TextInput(label="Role ID (optional)", required=False)

        self.add_item(self.item_name)
        self.add_item(self.price)
        self.add_item(self.role_id)

    async def on_submit(self, interaction: discord.Interaction):

        try:
            price = int(self.price.value)
        except:
            return await interaction.response.send_message("❌ Price must be a number.", ephemeral=True)

        item = {
            "name": self.item_name.value,
            "price": price
        }

        if self.role_id.value:
            item["role"] = self.role_id.value

        await self.bot.shop.update_one(
            {"guild_id": str(interaction.guild.id)},
            {"$push": {"items": item}},
            upsert=True
        )

        await interaction.response.send_message(
            f"✅ Added **{item['name']}** to shop!",
            ephemeral=True
        )


# =========================
# SELECT MENUS
# =========================
class MainSelect(discord.ui.Select):

    def __init__(self):
        options = [
            discord.SelectOption(label="admin_role", description="Set admin role"),
            discord.SelectOption(label="cooldown", description="Set command cooldown"),
            discord.SelectOption(label="income_role", description="Set income role"),
            discord.SelectOption(label="shop_item", description="Add shop items"),
        ]

        super().__init__(placeholder="Choose setting", options=options)

    async def callback(self, interaction: discord.Interaction):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Admin only", ephemeral=True)

        choice = self.values[0]

        if choice == "admin_role":
            await interaction.response.send_message(
                "Select admin role:",
                view=RoleView(interaction.guild.roles),
                ephemeral=True
            )

        elif choice == "cooldown":
            await interaction.response.send_message(
                "Select command:",
                view=CommandView(),
                ephemeral=True
            )

        elif choice == "income_role":
            await interaction.response.send_message(
                "Select income role:",
                view=IncomeRoleView(interaction.guild.roles),
                ephemeral=True
            )

        elif choice == "shop_item":
            await interaction.response.send_message(
                "🛒 Create a shop item:",
                view=ShopItemView(),
                ephemeral=True
            )


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

        super().__init__(placeholder="Select command", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            CooldownModal(self.values[0], interaction.client)
        )


class RoleSelect(discord.ui.Select):

    def __init__(self, roles):
        roles = roles[:25]

        options = [
            discord.SelectOption(label=r.name, value=str(r.id))
            for r in roles
        ]

        super().__init__(placeholder="Select role", options=options)

    async def callback(self, interaction: discord.Interaction):
        settings = await get_settings(interaction.client, interaction.guild.id)

        settings["admin_role_id"] = self.values[0]
        await save_settings(interaction.client, interaction.guild.id, settings)

        await interaction.response.send_message(
            f"🛡 Admin role set → <@&{self.values[0]}>",
            ephemeral=True
        )


class IncomeRoleSelect(discord.ui.Select):

    def __init__(self, roles):
        roles = roles[:25]

        options = [
            discord.SelectOption(label=r.name, value=str(r.id))
            for r in roles
        ]

        super().__init__(placeholder="Select income role", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            IncomeRoleModal(self.values[0], interaction.client)
        )


# =========================
# VIEWS
# =========================
class MainView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(MainSelect())


class CommandView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(CommandSelect())


class RoleView(discord.ui.View):
    def __init__(self, roles):
        super().__init__()
        self.add_item(RoleSelect(roles))


class IncomeRoleView(discord.ui.View):
    def __init__(self, roles):
        super().__init__()
        self.add_item(IncomeRoleSelect(roles))


class ShopItemView(discord.ui.View):

    def __init__(self):
        super().__init__()

    @discord.ui.button(label="➕ Create Shop Item", style=discord.ButtonStyle.green)
    async def create(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_modal(
            ShopItemModal(interaction.client)
        )


# =========================
# DASHBOARD
# =========================
class Dashboard(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="dashboard", description="Economy control panel")
    async def dashboard(self, interaction: discord.Interaction):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Admin only", ephemeral=True)

        settings = await get_settings(self.bot, interaction.guild.id)

        embed = discord.Embed(
            title="⚙️ Economy Dashboard",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="🛡 Admin Role",
            value=f"<@&{settings.get('admin_role_id')}>" if settings.get("admin_role_id") else "None",
            inline=False
        )

        embed.add_field(
            name="⏱ Cooldowns",
            value="\n".join([f"{k} → {v}s" for k, v in settings.get("cooldowns", {}).items()]) or "None",
            inline=False
        )

        embed.add_field(
            name="💼 Income Roles",
            value="\n".join([f"<@&{k}> → ${v}" for k, v in settings.get("role_income", {}).items()]) or "None",
            inline=False
        )

        # =========================
        # 🛒 SHOP DISPLAY (ADDED)
        # =========================
        shop_data = await self.bot.shop.find_one({"guild_id": str(interaction.guild.id)})

        embed.add_field(
            name="🛒 Shop Items",
            value=(
                "\n".join([
                    f"• {item['name']} - ${item['price']}" +
                    (f" (Role: <@&{item['role']}>)" if item.get("role") else "")
                    for item in (shop_data.get("items", []) if shop_data else [])
                ])
                if shop_data and shop_data.get("items")
                else "None"
            ),
            inline=False
        )

        await interaction.response.send_message(embed=embed, view=MainView())


async def setup(bot):
    await bot.add_cog(Dashboard(bot))