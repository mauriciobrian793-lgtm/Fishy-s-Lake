import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput
from utils import get_settings


# =========================
# SAVE SETTINGS
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

        self.amount = TextInput(label="Income amount per collect", placeholder="500")
        self.add_item(self.amount)

    async def on_submit(self, interaction: discord.Interaction):
        settings = await get_settings(self.bot, interaction.guild.id)

        try:
            amount = int(self.amount.value)
        except:
            return await interaction.response.send_message("❌ Invalid number", ephemeral=True)

        settings.setdefault("role_income", {})[self.role_id] = amount
        await save_settings(self.bot, interaction.guild.id, settings)

        await interaction.response.send_message(
            f"💰 Saved <@&{self.role_id}> → ${amount}",
            ephemeral=True
        )


class CooldownModal(discord.ui.Modal):
    def __init__(self, command, bot):
        super().__init__(title=f"⏱ Cooldown: {command}")
        self.command = command
        self.bot = bot

        self.seconds = TextInput(label="Seconds", placeholder="60")
        self.add_item(self.seconds)

    async def on_submit(self, interaction: discord.Interaction):
        settings = await get_settings(self.bot, interaction.guild.id)

        try:
            seconds = int(self.seconds.value)
        except:
            return await interaction.response.send_message("❌ Invalid number", ephemeral=True)

        settings.setdefault("cooldowns", {})[self.command] = seconds
        await save_settings(self.bot, interaction.guild.id, settings)

        await interaction.response.send_message(
            f"⏱ Saved {self.command} → {seconds}s",
            ephemeral=True
        )


# =========================
# SHOP ADD
# =========================
class ShopAddModal(discord.ui.Modal, title="🛒 Add Shop Item"):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

        self.name = TextInput(label="Item Name")
        self.price = TextInput(label="Price")
        self.role = TextInput(label="Role ID (optional)", required=False)

        self.add_item(self.name)
        self.add_item(self.price)
        self.add_item(self.role)

    async def on_submit(self, interaction: discord.Interaction):

        try:
            price = int(self.price.value)
        except:
            return await interaction.response.send_message("❌ Invalid price", ephemeral=True)

        item = {
            "name": self.name.value,
            "price": price
        }

        if self.role.value:
            item["role_id"] = self.role.value   # FIXED KEY

        await self.bot.shop.update_one(
            {"guild_id": str(interaction.guild.id)},
            {"$push": {"items": item}},
            upsert=True
        )

        await interaction.response.send_message("✅ Item added", ephemeral=True)


# =========================
# SHOP DELETE VIEW
# =========================
class ShopDeleteView(discord.ui.View):
    def __init__(self, bot, items):
        super().__init__(timeout=60)
        self.bot = bot

        options = [
            discord.SelectOption(
                label=f"{i['name']} - ${i['price']}",
                value=i["name"]
            )
            for i in items
        ]

        self.select = discord.ui.Select(
            placeholder="Select item to delete",
            options=options
        )

        self.select.callback = self.delete_callback
        self.add_item(self.select)

    async def delete_callback(self, interaction: discord.Interaction):

        shop = await self.bot.shop.find_one({"guild_id": str(interaction.guild.id)})

        selected = self.select.values[0]

        new_items = [i for i in shop.get("items", []) if i["name"] != selected]

        await self.bot.shop.update_one(
            {"guild_id": str(interaction.guild.id)},
            {"$set": {"items": new_items}}
        )

        await interaction.response.send_message(f"🗑 Deleted **{selected}**", ephemeral=True)


# =========================
# MAIN MENU
# =========================
class MainSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="admin_role"),
            discord.SelectOption(label="cooldown"),
            discord.SelectOption(label="income_role"),
            discord.SelectOption(label="shop_add"),
            discord.SelectOption(label="shop_delete"),
        ]

        super().__init__(placeholder="Choose setting", options=options)

    async def callback(self, interaction: discord.Interaction):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Admin only", ephemeral=True)

        choice = self.values[0]

        if choice == "admin_role":
            await interaction.response.send_message("Select role:", view=RoleView(interaction.guild.roles), ephemeral=True)

        elif choice == "cooldown":
            await interaction.response.send_message("Select command:", view=CommandView(), ephemeral=True)

        elif choice == "income_role":
            await interaction.response.send_message("Select role:", view=IncomeRoleView(interaction.guild.roles), ephemeral=True)

        elif choice == "shop_add":
            await interaction.response.send_modal(ShopAddModal(interaction.client))

        elif choice == "shop_delete":
            shop = await interaction.client.shop.find_one({"guild_id": str(interaction.guild.id)})

            if not shop or not shop.get("items"):
                return await interaction.response.send_message("❌ No items", ephemeral=True)

            await interaction.response.send_message(
                "🗑 Select item:",
                view=ShopDeleteView(interaction.client, shop["items"]),
                ephemeral=True
            )


# =========================
# SELECTS (UNCHANGED)
# =========================
class CommandSelect(discord.ui.Select): ...
class RoleSelect(discord.ui.Select): ...
class IncomeRoleSelect(discord.ui.Select): ...


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


class Dashboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="dashboard")
    async def dashboard(self, interaction: discord.Interaction):

        settings = await get_settings(self.bot, interaction.guild.id)
        shop = await self.bot.shop.find_one({"guild_id": str(interaction.guild.id)})

        embed = discord.Embed(title="⚙️ Economy Dashboard", color=discord.Color.blurple())

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

        embed.add_field(
            name="🛒 Shop Items",
            value="\n".join([
                f"{i['name']} - ${i['price']}" +
                (f" | <@&{i['role_id']}>" if i.get("role_id") else "")
                for i in (shop.get("items", []) if shop else [])
            ]) or "None",
            inline=False
        )

        await interaction.response.send_message(embed=embed, view=MainView())


async def setup(bot):
    await bot.add_cog(Dashboard(bot))