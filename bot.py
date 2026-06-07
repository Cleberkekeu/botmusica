import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os

# ── Token: lê de variável de ambiente ou arquivo .env ──────────
def get_token():
    # Railway/cloud: variável de ambiente TOKEN
    token = os.environ.get("TOKEN")
    if token:
        return token
    # Local: lê do arquivo .env
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                if line.startswith("TOKEN="):
                    return line.strip().split("=", 1)[1]
    # Primeira vez: pergunta e salva
    print("\n" + "="*50)
    print("PRIMEIRA CONFIGURACAO DO BOT")
    print("="*50)
    print("\nPara obter seu token:")
    print("1. Acesse: https://discord.com/developers/applications")
    print("2. Clique no seu bot > Bot > Reset Token")
    print("3. Copie o token e cole abaixo\n")
    token = input("Cole seu token aqui: ").strip()
    with open(".env", "w") as f:
        f.write(f"TOKEN={token}\n")
    print("\nToken salvo! Nao precisara fazer isso novamente.\n")
    return token

TOKEN = get_token()
# ───────────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

YDL_OPTS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
    "extractor_args": {"youtube": {"player_client": ["ios"]}},
    "http_headers": {
        "User-Agent": "com.google.ios.youtube/19.29.1 (iPhone16,2; U; CPU iOS 17_5_1 like Mac OS X;)"
    },
}

FFMPEG_OPTS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}


def get_audio_url(query: str) -> tuple[str, str]:
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        info = ydl.extract_info(query, download=False)
        if "entries" in info:
            info = info["entries"][0]
        return info["url"], info.get("title", "Desconhecido")


@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}!")
    print("   Use !play <música> no Discord para tocar música.")
    print("   Pressione Ctrl+C para parar o bot.\n")


@bot.command(name="play", aliases=["p"])
async def play(ctx: commands.Context, *, query: str):
    if not ctx.author.voice:
        await ctx.send("❌ Entre em um canal de voz primeiro!")
        return

    voice_channel = ctx.author.voice.channel

    if ctx.voice_client is None:
        await voice_channel.connect()
    elif ctx.voice_client.channel != voice_channel:
        await ctx.voice_client.move_to(voice_channel)

    vc = ctx.voice_client

    if vc.is_playing():
        vc.stop()

    msg = await ctx.send(f"🔍 Buscando: **{query}**...")

    try:
        audio_url, title = await asyncio.to_thread(get_audio_url, query)
    except Exception as e:
        await msg.edit(content=f"❌ Erro ao buscar a música: {e}")
        return

    source = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTS)
    vc.play(source)
    await msg.edit(content=f"🎵 Tocando agora: **{title}**")


@bot.command(name="stop", aliases=["s"])
async def stop(ctx: commands.Context):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        await ctx.send("⏹️ Parado e desconectado.")
    else:
        await ctx.send("❌ O bot não está em nenhum canal de voz.")


@bot.command(name="pause")
async def pause(ctx: commands.Context):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Pausado.")
    else:
        await ctx.send("❌ Nenhuma música tocando.")


@bot.command(name="resume")
async def resume(ctx: commands.Context):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Retomado.")
    else:
        await ctx.send("❌ Nenhuma música pausada.")


@bot.command(name="skip")
async def skip(ctx: commands.Context):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ Pulado.")
    else:
        await ctx.send("❌ Nenhuma música tocando.")


bot.run(TOKEN)
