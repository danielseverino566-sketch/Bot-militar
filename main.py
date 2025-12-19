import discord
from discord.ext import commands
from discord.ui import View, Modal, TextInput, Select
import os

# ================= CONFIG =================

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

CARGOS_AUTORIZADOS = [1285060678817943553]  # ID do cargo autorizado

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

# ================= MODALS =================

class TituloModal(Modal, title="📌 Definir Título"):
    titulo = TextInput(label="Título do anúncio", max_length=256)

    async def on_submit(self, interaction):
        get_dados(interaction.user.id)["titulo"] = self.titulo.value
        await interaction.response.send_message("✔️ Título definido.", ephemeral=True)

class MensagemModal(Modal, title="📝 Definir Mensagem"):
    mensagem = TextInput(
        label="Mensagem do anúncio",
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction):
        get_dados(interaction.user.id)["mensagem"] = self.mensagem.value
        await interaction.response.send_message("✔️ Mensagem definida.", ephemeral=True)

class ImagemModal(Modal, title="🖼️ Definir Imagem (opcional)"):
    imagem = TextInput(
        label="URL da imagem",
        required=False
    )

    async def on_submit(self, interaction):
        get_dados(interaction.user.id)["imagem"] = self.imagem.value or None
        await interaction.response.send_message("✔️ Imagem definida.", ephemeral=True)

# ================= SELECT CANAL =================

class CanalSelect(Select):
    def __init__(self, guild):
        options = [
            discord.SelectOption(
                label=f"#{c.name}",
                value=str(c.id)
            )
            for c in guild.text_channels[:25]
        ]
        super().__init__(
            placeholder="📍 Escolha o canal",
            options=options
        )

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
            await interaction.response.send_message(
                "❌ Selecione um canal.",
                ephemeral=True
            )
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

        await interaction.response.send_message("✅ Anúncio enviado.", ephemeral=True)

# ================= COMANDO =================

@bot.command()
async def painel(ctx):
    if not any(r.id in CARGOS_AUTORIZADOS for r in ctx.author.roles):
        await ctx.send("⛔ Você não tem permissão.")
        return

    await ctx.send(
        "🎛️ **PAINEL DE ANÚNCIOS**",
        view=Painel(ctx.author.id, ctx.guild)
    )

# ================= START =================

@bot.event
async def on_ready():
    print(f"🟢 Bot online: {bot.user}")

import os

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise RuntimeError("TOKEN não encontrado nas variáveis de ambiente")

bot.run(TOKEN)
