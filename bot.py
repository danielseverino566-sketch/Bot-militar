import discord
from discord.ext import commands
from discord.ui import View, Modal, TextInput, Select
from datetime import datetime
import os

# ================= CONFIG =================

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.voice_states = True
intents.messages = True
intents.bans = True

bot = commands.Bot(command_prefix="!", intents=intents)

CARGOS_AUTORIZADOS = [1285060678817943553]
LOG_CHANNEL_NAME = "<#1361000767741235331>"

# ================= UTIL LOG =================

def get_event_channel(guild):
    return discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)

async def log_event(guild, title, description, color):
    if not guild:
        return
    channel = get_event_channel(guild)
    if not channel:
        return

    embed = discord.Embed(
        title=title,
        description=description[:4000],
        color=color,
        timestamp=datetime.utcnow()
    )
    await channel.send(embed=embed)

# ================= DADOS =================

dados = {}

def get_dados(uid):
    if uid not in dados:
        dados[uid] = {
            "titulo": "SEM TÍTULO",
            "mensagem": "Nenhuma mensagem definida.",
            "imagem": None,
            "cor": discord.Color.dark_green(),
            "canal": None,
            "marcacao": None
        }
    return dados[uid]

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

class MarcacaoModal(Modal, title="🎖️ MARCAÇÃO"):
    marcacao = TextInput(label="Marcação", required=False)

    async def on_submit(self, interaction):
        get_dados(interaction.user.id)["marcacao"] = self.marcacao.value or None
        await interaction.response.send_message("✔️ Marcação definida.", ephemeral=True)

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
        await interaction.response.send_message("📍 Canal selecionado.", ephemeral=True)

# ================= VIEW =================

class PainelMilitar(View):
    def __init__(self, autor_id, guild):
        super().__init__(timeout=None)
        self.autor_id = autor_id
        self.guild = guild
        self.add_item(CanalSelect(guild))

    async def interaction_check(self, interaction):
        return interaction.user.id == self.autor_id

    @discord.ui.button(label="✏️ TÍTULO", style=discord.ButtonStyle.primary)
    async def titulo(self, interaction, _):
        await interaction.response.send_modal(TituloModal())

    @discord.ui.button(label="📝 MENSAGEM", style=discord.ButtonStyle.success)
    async def mensagem(self, interaction, _):
        await interaction.response.send_modal(MensagemModal())

    @discord.ui.button(label="🎖️ MARCAÇÃO", style=discord.ButtonStyle.secondary)
    async def marcacao(self, interaction, _):
        await interaction.response.send_modal(MarcacaoModal())

    @discord.ui.button(label="🖼️ IMAGEM", style=discord.ButtonStyle.secondary)
    async def imagem(self, interaction, _):
        await interaction.response.send_modal(ImagemModal())

    @discord.ui.button(label="👁️ PRÉ-VISUALIZAR", style=discord.ButtonStyle.secondary, row=1)
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
        canal = self.guild.get_channel(info["canal"])
        if not canal:
            await interaction.response.send_message("❌ Canal inválido.", ephemeral=True)
            return

        embed = discord.Embed(
            title=info["titulo"],
            description=info["mensagem"],
            color=info["cor"]
        )
        embed.set_footer(text=f"Ordem emitida por {interaction.user}")

        if info["imagem"]:
            embed.set_image(url=info["imagem"])

        await canal.send(content=info["marcacao"], embed=embed)
        dados.pop(interaction.user.id, None)
        await interaction.response.send_message("✅ Comunicado enviado.", ephemeral=True)

# ================= COMANDO =================

@bot.command()
async def painel(ctx):
    if not any(r.id in CARGOS_AUTORIZADOS for r in ctx.author.roles):
        await ctx.send("⛔ Acesso negado.")
        return

    await ctx.send("🎛️ PAINEL MILITAR", view=PainelMilitar(ctx.author.id, ctx.guild))

# ================= LOGS =================

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content[:1800] if message.content else "Mensagem vazia"

    await log_event(
        message.guild,
        "📝 Mensagem enviada",
        f"👤 {message.author}\n📍 {message.channel.mention}\n```{content}```",
        discord.Color.blue()
    )
    await bot.process_commands(message)

@bot.event
async def on_message_edit(before, after):
    if before.author.bot:
        return

    await log_event(
        before.guild,
        "✏️ Mensagem editada",
        f"👤 {before.author}\n```{before.content}```\n➡️\n```{after.content}```",
        discord.Color.orange()
    )

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return

    await log_event(
        message.guild,
        "🗑️ Mensagem apagada",
        f"👤 {message.author}\n```{message.content}```",
        discord.Color.red()
    )

@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel != after.channel:
        await log_event(
            member.guild,
            "🎙️ Voz",
            f"{member}\n{before.channel} ➜ {after.channel}",
            discord.Color.green()
        )

@bot.event
async def on_member_update(before, after):
    for role in set(after.roles) - set(before.roles):
        await log_event(after.guild, "➕ Cargo adicionado", f"{after} → {role}", discord.Color.green())
    for role in set(before.roles) - set(after.roles):
        await log_event(after.guild, "➖ Cargo removido", f"{after} → {role}", discord.Color.red())

@bot.event
async def on_member_join(member):
    await log_event(member.guild, "👤 Entrou no servidor", str(member), discord.Color.green())

@bot.event
async def on_member_remove(member):
    await log_event(member.guild, "🚪 Saiu do servidor", str(member), discord.Color.red())

# ================= START =================

@bot.event
async def on_ready():
    print(f"🪖 Bot online: {bot.user}")

TOKEN = os.environ["TOKEN"]
bot.run(TOKEN)
