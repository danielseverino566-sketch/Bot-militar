import discord
from discord.ext import commands
from discord.ui import View, Modal, TextInput, Select
import os
from datetime import datetime

# ================= CONFIG =================

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

CARGOS_AUTORIZADOS = [1285060678817943553]
LOG_CHANNEL_ID = 1361000767741235331  # 【🔧】evento

# ================= DADOS =================

dados = {}

def get_dados(uid):
    if uid not in dados:
        dados[uid] = {
            "titulo": "SEM TÍTULO",
            "mensagem": "Nenhuma mensagem definida.",
            "imagem": None,
            "cor": discord.Color.dark_green(),
            "canal": None
        }
    return dados[uid]

# ================= LOG FUNÇÃO =================

async def log_event(guild, title, description, color):
    channel = guild.get_channel(LOG_CHANNEL_ID)
    if not channel:
        return

    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.utcnow()
    )
    await channel.send(embed=embed)

# ================= MODALS =================

class TituloModal(Modal, title="📌 TÍTULO"):
    titulo = TextInput(label="Título", max_length=256)

    async def on_submit(self, interaction):
        get_dados(interaction.user.id)["titulo"] = self.titulo.value
        await interaction.response.send_message("✔️ Título definido.", ephemeral=True)

class MensagemModal(Modal, title="📝 MENSAGEM"):
    mensagem = TextInput(label="Mensagem", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction):
        get_dados(interaction.user.id)["mensagem"] = self.mensagem.value
        await interaction.response.send_message("✔️ Mensagem definida.", ephemeral=True)

class ImagemModal(Modal, title="🖼️ IMAGEM"):
    imagem = TextInput(label="URL da imagem", required=False)

    async def on_submit(self, interaction):
        get_dados(interaction.user.id)["imagem"] = self.imagem.value or None
        await interaction.response.send_message("✔️ Imagem definida.", ephemeral=True)

# ================= SELECT =================

class CanalSelect(Select):
    def __init__(self, guild):
        options = [
            discord.SelectOption(label=f"#{c.name}", value=str(c.id))
            for c in guild.text_channels[:25]
        ]
        super().__init__(placeholder="📍 CANAL", options=options)

    async def callback(self, interaction):
        get_dados(interaction.user.id)["canal"] = int(self.values[0])
        await interaction.response.send_message("📍 Canal definido.", ephemeral=True)

# ================= PAINEL =================

class Painel(View):
    def __init__(self, autor, guild):
        super().__init__(timeout=None)
        self.autor = autor
        self.guild = guild
        self.add_item(CanalSelect(guild))

    async def interaction_check(self, interaction):
        return interaction.user.id == self.autor

    @discord.ui.button(label="✏️ TÍTULO", style=discord.ButtonStyle.primary)
    async def titulo(self, interaction, _):
        await interaction.response.send_modal(TituloModal())

    @discord.ui.button(label="📝 MENSAGEM", style=discord.ButtonStyle.success)
    async def mensagem(self, interaction, _):
        await interaction.response.send_modal(MensagemModal())

    @discord.ui.button(label="🖼️ IMAGEM", style=discord.ButtonStyle.secondary)
    async def imagem(self, interaction, _):
        await interaction.response.send_modal(ImagemModal())

    @discord.ui.button(label="👁️ PRÉVIA", style=discord.ButtonStyle.secondary, row=1)
    async def preview(self, interaction, _):
        info = get_dados(interaction.user.id)
        embed = discord.Embed(
            title=info["titulo"],
            description=info["mensagem"],
            color=info["cor"]
        )
        if info["imagem"]:
            embed.set_image(url=info["imagem"])
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="📤 ENVIAR", style=discord.ButtonStyle.danger, row=1)
    async def enviar(self, interaction, _):
        info = get_dados(interaction.user.id)
        if not info["canal"]:
            await interaction.response.send_message("❌ Selecione um canal.", ephemeral=True)
            return

        canal = self.guild.get_channel(info["canal"])
        embed = discord.Embed(
            title=info["titulo"],
            description=info["mensagem"],
            color=info["cor"]
        )
        embed.set_footer(text=f"Emitido por {interaction.user}")

        if info["imagem"]:
            embed.set_image(url=info["imagem"])

        await canal.send(embed=embed)
        dados.pop(interaction.user.id, None)
        await interaction.response.send_message("✅ Enviado.", ephemeral=True)

# ================= COMANDO =================

@bot.command()
async def painel(ctx):
    if not any(r.id in CARGOS_AUTORIZADOS for r in ctx.author.roles):
        await ctx.send("⛔ Acesso negado.")
        return

    await ctx.send("🎛️ **PAINEL MILITAR**", view=Painel(ctx.author.id, ctx.guild))

# ================= EVENTOS =================

@bot.event
async def on_ready():
    print(f"🟢 Online: {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    await log_event(
        message.guild,
        "📝 Mensagem enviada",
        f"{message.author}\n{message.channel.mention}\n```{message.content}```",
        discord.Color.blue()
    )
    await bot.process_commands(message)

@bot.event
async def on_message_edit(before, after):
    if before.author.bot or before.content == after.content:
        return

    await log_event(
        before.guild,
        "✏️ Mensagem editada",
        f"{before.author}\n```{before.content}``` → ```{after.content}```",
        discord.Color.orange()
    )

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return

    await log_event(
        message.guild,
        "🗑️ Mensagem apagada",
        f"{message.author}\n```{message.content}```",
        discord.Color.red()
    )

@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel == after.channel:
        return

    msg = f"{member} "
    if not before.channel and after.channel:
        msg += f"entrou em {after.channel.name}"
    elif before.channel and not after.channel:
        msg += f"saiu de {before.channel.name}"
    else:
        msg += f"mudou {before.channel.name} → {after.channel.name}"

    await log_event(member.guild, "🎙️ Voz", msg, discord.Color.green())

@bot.event
async def on_member_update(before, after):
    for role in set(after.roles) - set(before.roles):
        await log_event(after.guild, "➕ Cargo", f"{after} + {role.name}", discord.Color.green())

    for role in set(before.roles) - set(after.roles):
        await log_event(after.guild, "➖ Cargo", f"{after} - {role.name}", discord.Color.red())

@bot.event
async def on_member_join(member):
    await log_event(member.guild, "👤 Entrou", f"{member}", discord.Color.green())

@bot.event
async def on_member_remove(member):
    await log_event(member.guild, "🚪 Saiu", f"{member}", discord.Color.red())

# ================= START =================

bot.run(os.environ["TOKEN"])
