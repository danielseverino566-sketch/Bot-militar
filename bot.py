import discord
from discord.ext import commands
from discord.ui import View, Modal, TextInput, Select
import os

# ================= CONFIG =================

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

CARGOS_AUTORIZADOS = [1285060678817943553]

# ================= DADOS POR USUÁRIO =================

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

class TituloModal(Modal, title="📌 TÍTULO DO COMUNICADO"):
    titulo = TextInput(label="Título", max_length=256)

    async def on_submit(self, interaction: discord.Interaction):
        get_dados(interaction.user.id)["titulo"] = self.titulo.value
        await interaction.response.send_message("✔️ Título definido.", ephemeral=True)

class MensagemModal(Modal, title="📝 TEXTO DO COMUNICADO"):
    mensagem = TextInput(label="Mensagem", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        get_dados(interaction.user.id)["mensagem"] = self.mensagem.value
        await interaction.response.send_message("✔️ Mensagem definida.", ephemeral=True)

class ImagemModal(Modal, title="🖼️ IMAGEM (Opcional)"):
    imagem = TextInput(label="URL da imagem", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        get_dados(interaction.user.id)["imagem"] = self.imagem.value or None
        await interaction.response.send_message("✔️ Imagem definida.", ephemeral=True)

class MarcacaoModal(Modal, title="🎖️ MARCAÇÃO (Opcional)"):
    marcacao = TextInput(
        label="Digite a marcação",
        placeholder="Ex: @militares ou @everyone",
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        get_dados(interaction.user.id)["marcacao"] = self.marcacao.value or None
        await interaction.response.send_message("✔️ Marcação definida.", ephemeral=True)

# ================= SELECT =================

class CanalSelect(Select):
    def __init__(self, guild):
        options = [
            discord.SelectOption(label=f"#{c.name}", value=str(c.id))
            for c in guild.text_channels[:25]
        ]
        super().__init__(placeholder="📍 CANAL DE ENVIO", options=options)

    async def callback(self, interaction: discord.Interaction):
        get_dados(interaction.user.id)["canal"] = int(self.values[0])
        await interaction.response.send_message("📍 Canal selecionado.", ephemeral=True)

# ================= PAINEL =================

class PainelMilitar(View):
    def __init__(self, autor_id, guild):
        super().__init__(timeout=None)
        self.autor_id = autor_id
        self.guild = guild
        self.add_item(CanalSelect(guild))

    async def interaction_check(self, interaction: discord.Interaction):
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

    @discord.ui.button(label="🟢 INFORMATIVO", style=discord.ButtonStyle.success, row=1)
    async def verde(self, interaction, _):
        get_dados(interaction.user.id)["cor"] = discord.Color.dark_green()
        await interaction.response.send_message("🟢 Cor definida.", ephemeral=True)

    @discord.ui.button(label="🔵 DIRETRIZ", style=discord.ButtonStyle.primary, row=1)
    async def azul(self, interaction, _):
        get_dados(interaction.user.id)["cor"] = discord.Color.dark_blue()
        await interaction.response.send_message("🔵 Cor definida.", ephemeral=True)

    @discord.ui.button(label="🔴 ALERTA", style=discord.ButtonStyle.danger, row=1)
    async def vermelho(self, interaction, _):
        get_dados(interaction.user.id)["cor"] = discord.Color.dark_red()
        await interaction.response.send_message("🔴 Cor definida.", ephemeral=True)

    @discord.ui.button(label="👁️ PRÉ-VISUALIZAR", style=discord.ButtonStyle.secondary, row=2)
    async def preview(self, interaction, _):
        info = get_dados(interaction.user.id)
        embed = discord.Embed(
            title=f"📢 {info['titulo']}",
            description=info["mensagem"],
            color=info["cor"]
        )
        if info["imagem"]:
            embed.set_image(url=info["imagem"])

        await interaction.response.send_message(
            "📄 **PRÉ-VISUALIZAÇÃO**",
            embed=embed,
            ephemeral=True
        )

    @discord.ui.button(label="📤 ENVIAR COMUNICADO", style=discord.ButtonStyle.danger, row=2)
    async def enviar(self, interaction, _):
        info = get_dados(interaction.user.id)

        if not info["canal"]:
            await interaction.response.send_message("❌ Selecione um canal.", ephemeral=True)
            return

        canal = self.guild.get_channel(info["canal"])
        if not canal:
            await interaction.response.send_message("❌ Canal inválido.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"📢 {info['titulo']}",
            description=info["mensagem"],
            color=info["cor"]
        )
        embed.set_footer(text=f"Ordem emitida por {interaction.user} • Sistema Militar")

        if info["imagem"]:
            embed.set_image(url=info["imagem"])

        await canal.send(embed=embed)

        dados.pop(interaction.user.id, None)
        await interaction.response.send_message("✅ Comunicado enviado.", ephemeral=True)

# ================= COMANDO =================

@bot.command()
async def painel(ctx):
    if not any(role.id in CARGOS_AUTORIZADOS for role in ctx.author.roles):
        await ctx.send("⛔ **ACESSO NEGADO**\nPainel restrito ao Alto Comando.")
        return

    await ctx.send(
        "🎛️ **PAINEL MILITAR DE COMUNICAÇÕES OFICIAIS**",
        view=PainelMilitar(ctx.author.id, ctx.guild)
    )

# ================= EVENTO =================

@bot.event
async def on_ready():
    print(f"🪖 Bot Militar Online: {bot.user}")

# ================= INICIAR BOT =================

TOKEN = os.environ["TOKEN"]
bot.run(TOKEN)
