import discord
from discord.ext import commands
import asyncio
import random
import datetime
import os
import aiohttp
import io
from dotenv import load_dotenv

try:
    from ocr import GoogleOCR
    OCR_AVAILABLE = True
except ImportError:
    print("⚠️ GoogleOCR não disponível. Comandos de OCR serão desabilitados.")
    OCR_AVAILABLE = False

class ApoiadorBot:
    def __init__(self):

        env_path = "./config/.env"
        load_dotenv(dotenv_path=env_path)

        print(f"Arquivo .env encontrado: {os.path.exists(env_path)}")
        print(f"Token carregado: {'Sim' if os.getenv('DISCORD_TOKEN') else 'Não'}")
        print(f"Primeiros caracteres do token: {os.getenv('DISCORD_TOKEN')[:10] if os.getenv('DISCORD_TOKEN') else 'None'}")
                
        # Configurar intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        # Criar o bot
        self.bot = commands.Bot(command_prefix='!', intents=intents)
        
        # Inicializar OCR se disponível
        self.ocr = None
        if OCR_AVAILABLE:
            credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH')
            if credentials_path and os.path.exists(credentials_path):
                try:
                    self.ocr = GoogleOCR(credentials_path)
                    print("✅ OCR configurado com sucesso!")
                except Exception as e:
                    print(f"❌ Erro ao configurar OCR: {e}")
            else:
                print("⚠️ Credenciais do Google Cloud não encontradas.")
        
        # Configurar eventos e comandos
        self.setup_events()
        self.setup_commands()
        self.setup_ocr_commands()
    
    def setup_events(self):
        """Configura todos os eventos do bot"""
        
        @self.bot.event
        async def on_ready():
            print(f'{self.bot.user} está online!')
            status_text = "Digite !ajuda"
            if self.ocr:
                status_text += " | OCR disponível"
            await self.bot.change_presence(activity=discord.Game(name=status_text))
        
        @self.bot.event
        async def on_member_join(member):
            channel = discord.utils.get(member.guild.channels, name='geral')
            if channel:
                embed = discord.Embed(
                    title="Bem-vindo!",
                    description=f"Olá {member.mention}! Bem-vindo ao servidor!",
                    color=0x00ff00
                )
                await channel.send(embed=embed)
        
        @self.bot.event
        async def on_command_error(ctx, error):
            if isinstance(error, commands.CommandNotFound):
                embed = discord.Embed(
                    title="❌ Comando não encontrado",
                    description="Use `!ajuda` para ver os comandos disponíveis.",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
            elif isinstance(error, commands.MissingPermissions):
                embed = discord.Embed(
                    title="🚫 Sem permissão",
                    description="Você não tem permissão para usar este comando.",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
            else:
                # Log outros erros
                print(f"Erro no comando: {error}")
    
    def setup_commands(self):
        """Configura todos os comandos básicos do bot"""
        
        @self.bot.command(name='ping')
        async def ping(ctx):
            latency = round(self.bot.latency * 1000)
            embed = discord.Embed(
                title="🏓 Pong!",
                description=f"Latência: {latency}ms",
                color=0x0099ff
            )
            await ctx.send(embed=embed)
        
        @self.bot.command(name='servidor')
        async def server_info(ctx):
            guild = ctx.guild
            embed = discord.Embed(
                title=f"Informações do {guild.name}",
                color=0xff9900
            )
            embed.add_field(name="👑 Dono", value=guild.owner.mention, inline=True)
            embed.add_field(name="👥 Membros", value=guild.member_count, inline=True)
            embed.add_field(name="📅 Criado em", value=guild.created_at.strftime("%d/%m/%Y"), inline=True)
            embed.add_field(name="💬 Canais de texto", value=len(guild.text_channels), inline=True)
            embed.add_field(name="🔊 Canais de voz", value=len(guild.voice_channels), inline=True)
            embed.add_field(name="😊 Emojis", value=len(guild.emojis), inline=True)
            
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            
            await ctx.send(embed=embed)
        
        @self.bot.command(name='dado')
        async def roll_dice(ctx, sides: int = 6):
            if sides < 2:
                await ctx.send("O dado precisa ter pelo menos 2 lados!")
                return
            
            result = random.randint(1, sides)
            embed = discord.Embed(
                title="🎲 Rolagem de Dado",
                description=f"Você rolou um dado de {sides} lados e tirou: **{result}**",
                color=0xff0000
            )
            await ctx.send(embed=embed)
        
        @self.bot.command(name='moeda')
        async def flip_coin(ctx):
            result = random.choice(['Cara', 'Coroa'])
            emoji = '🪙' if result == 'Cara' else '🌙'
            
            embed = discord.Embed(
                title=f"{emoji} Cara ou Coroa",
                description=f"A moeda caiu em: **{result}**",
                color=0xffd700
            )
            await ctx.send(embed=embed)
        
        @self.bot.command(name='enquete')
        async def poll(ctx, *, question):
            embed = discord.Embed(
                title="📊 Enquete",
                description=question,
                color=0x9932cc
            )
            embed.set_footer(text=f"Enquete criada por {ctx.author.display_name}")
            
            msg = await ctx.send(embed=embed)
            await msg.add_reaction('✅')
            await msg.add_reaction('❌')
        
        @self.bot.command(name='limpar')
        @commands.has_permissions(manage_messages=True)
        async def clear_messages(ctx, amount: int = 5):
            if amount > 100:
                await ctx.send("Não posso deletar mais de 100 mensagens por vez!")
                return
            
            deleted = await ctx.channel.purge(limit=amount + 1)
            
            embed = discord.Embed(
                title="🧹 Mensagens Limpas",
                description=f"Deletei {len(deleted) - 1} mensagens!",
                color=0x00ff00
            )
            msg = await ctx.send(embed=embed)
            await asyncio.sleep(3)
            await msg.delete()
        
        @self.bot.command(name='avatar')
        async def avatar(ctx, member: discord.Member = None):
            if member is None:
                member = ctx.author
            
            embed = discord.Embed(
                title=f"Avatar de {member.display_name}",
                color=0x00ffff
            )
            embed.set_image(url=member.avatar.url if member.avatar else member.default_avatar.url)
            await ctx.send(embed=embed)
        
        @self.bot.command(name='tempo')
        async def current_time(ctx):
            now = datetime.datetime.now()
            embed = discord.Embed(
                title="🕐 Horário Atual",
                description=now.strftime("**Data:** %d/%m/%Y\n**Horário:** %H:%M:%S"),
                color=0x4169e1
            )
            await ctx.send(embed=embed)
    
    def setup_ocr_commands(self):
        """Configura comandos relacionados ao OCR"""
        
        @self.bot.command(name='ocr')
        async def ocr_command(ctx):
            """Extrai texto de uma imagem anexada ou URL"""
            if not self.ocr:
                embed = discord.Embed(
                    title="❌ OCR Indisponível",
                    description="O serviço de OCR não está configurado. Verifique as credenciais do Google Cloud.",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
                return
            
            # Verificar se há anexos na mensagem
            if ctx.message.attachments:
                attachment = ctx.message.attachments[0]
                
                # Verificar se é uma imagem
                if not any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']):
                    embed = discord.Embed(
                        title="❌ Formato Inválido",
                        description="Por favor, envie uma imagem válida (PNG, JPG, JPEG, GIF, BMP, WEBP).",
                        color=0xff0000
                    )
                    await ctx.send(embed=embed)
                    return
                
                # Mostrar que está processando
                processing_embed = discord.Embed(
                    title="🔄 Processando...",
                    description="Extraindo texto da imagem, aguarde...",
                    color=0xffff00
                )
                processing_msg = await ctx.send(embed=processing_embed)
                
                try:
                    # Baixar a imagem
                    async with aiohttp.ClientSession() as session:
                        async with session.get(attachment.url) as resp:
                            if resp.status == 200:
                                image_data = await resp.read()
                            else:
                                raise Exception("Erro ao baixar a imagem")
                    
                    # Processar OCR
                    texts = self.ocr.perform_ocr(image_data)
                    
                    if texts and len(texts) > 0:
                        extracted_text = texts[0].description
                        
                        # Limitar tamanho do texto para Discord
                        if len(extracted_text) > 1900:
                            extracted_text = extracted_text[:1900] + "..."
                        
                        embed = discord.Embed(
                            title="📝 Texto Extraído",
                            description=f"```\n{extracted_text}\n```",
                            color=0x00ff00
                        )
                        embed.add_field(
                            name="📊 Estatísticas",
                            value=f"**Caracteres:** {len(texts[0].description)}\n**Palavras:** {len(texts[0].description.split())}\n**Elementos detectados:** {len(texts)}",
                            inline=False
                        )
                        embed.set_footer(text=f"Solicitado por {ctx.author.display_name}")
                        
                        await processing_msg.edit(embed=embed)
                        
                        # Se o texto for muito longo, enviar como arquivo
                        if len(texts[0].description) > 1900:
                            text_file = io.StringIO(texts[0].description)
                            file = discord.File(text_file, filename="texto_extraido.txt")
                            await ctx.send("📎 Texto completo:", file=file)
                    
                    else:
                        embed = discord.Embed(
                            title="❌ Nenhum Texto Encontrado",
                            description="Não foi possível detectar texto na imagem.",
                            color=0xff9900
                        )
                        await processing_msg.edit(embed=embed)
                
                except Exception as e:
                    embed = discord.Embed(
                        title="❌ Erro no Processamento",
                        description=f"Ocorreu um erro ao processar a imagem: {str(e)}",
                        color=0xff0000
                    )
                    await processing_msg.edit(embed=embed)
            
            else:
                embed = discord.Embed(
                    title="📷 Como usar o OCR",
                    description="Para extrair texto de uma imagem:",
                    color=0x0099ff
                )
                embed.add_field(
                    name="📤 Anexar Imagem",
                    value="Envie o comando `!ocr` junto com uma imagem anexada",
                    inline=False
                )
                embed.add_field(
                    name="🔗 URL da Imagem",
                    value="Use `!ocr_url <link_da_imagem>`",
                    inline=False
                )
                embed.add_field(
                    name="📋 Formatos Suportados",
                    value="PNG, JPG, JPEG, GIF, BMP, WEBP",
                    inline=False
                )
                await ctx.send(embed=embed)
        
        @self.bot.command(name='ocr_url')
        async def ocr_url_command(ctx, url: str = None):
            """Extrai texto de uma imagem via URL"""
            if not self.ocr:
                embed = discord.Embed(
                    title="❌ OCR Indisponível",
                    description="O serviço de OCR não está configurado.",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
                return
            
            if not url:
                embed = discord.Embed(
                    title="❌ URL Necessária",
                    description="Use: `!ocr_url <link_da_imagem>`",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
                return
            
            # Mostrar que está processando
            processing_embed = discord.Embed(
                title="🔄 Processando...",
                description="Baixando e processando imagem da URL...",
                color=0xffff00
            )
            processing_msg = await ctx.send(embed=processing_embed)
            
            try:
                # Usar o método process_image_url da classe OCR
                result = self.ocr.process_image_url(url, output_format='structured')
                
                if result and result.get('text'):
                    extracted_text = result['text']
                    
                    # Limitar tamanho do texto para Discord
                    display_text = extracted_text
                    if len(extracted_text) > 1900:
                        display_text = extracted_text[:1900] + "..."
                    
                    embed = discord.Embed(
                        title="📝 Texto Extraído da URL",
                        description=f"```\n{display_text}\n```",
                        color=0x00ff00
                    )
                    embed.add_field(
                        name="📊 Estatísticas",
                        value=f"**Caracteres:** {len(extracted_text)}\n**Palavras:** {result.get('word_count', 0)}\n**Confiança:** {result.get('confidence', 0):.2f}",
                        inline=False
                    )
                    embed.set_footer(text=f"Solicitado por {ctx.author.display_name}")
                    
                    await processing_msg.edit(embed=embed)
                    
                    # Se o texto for muito longo, enviar como arquivo
                    if len(extracted_text) > 1900:
                        text_file = io.StringIO(extracted_text)
                        file = discord.File(text_file, filename="texto_extraido_url.txt")
                        await ctx.send("📎 Texto completo:", file=file)
                
                else:
                    embed = discord.Embed(
                        title="❌ Nenhum Texto Encontrado",
                        description="Não foi possível detectar texto na imagem da URL.",
                        color=0xff9900
                    )
                    await processing_msg.edit(embed=embed)
            
            except Exception as e:
                embed = discord.Embed(
                    title="❌ Erro no Processamento",
                    description=f"Erro ao processar imagem da URL: {str(e)}",
                    color=0xff0000
                )
                await processing_msg.edit(embed=embed)
        
        @self.bot.command(name='ocr_status')
        async def ocr_status(ctx):
            """Mostra o status do serviço OCR"""
            embed = discord.Embed(
                title="🔍 Status do OCR",
                color=0x0099ff
            )
            
            if self.ocr:
                embed.add_field(name="✅ Status", value="OCR Configurado e Funcionando", inline=False)
                embed.add_field(name="🔧 Serviço", value="Google Cloud Vision API", inline=True)
                embed.add_field(name="📋 Recursos", value="Detecção de texto, Análise de documentos", inline=True)
            else:
                embed.add_field(name="❌ Status", value="OCR Não Disponível", inline=False)
                embed.add_field(name="⚠️ Motivo", value="Credenciais não configuradas", inline=False)
            
            await ctx.send(embed=embed)
    
    def setup_help_command(self):
        """Atualiza o comando de ajuda para incluir OCR"""
        
        @self.bot.command(name='ajuda')
        async def help_command(ctx):
            embed = discord.Embed(
                title="🤖 Comandos do Bot",
                description="Aqui estão todos os comandos disponíveis:",
                color=0xff6347
            )
            
            # Comandos básicos
            basic_commands = [
                ("!ping", "Mostra a latência do bot"),
                ("!servidor", "Informações do servidor"),
                ("!dado [lados]", "Rola um dado (padrão: 6 lados)"),
                ("!moeda", "Cara ou coroa"),
                ("!enquete <pergunta>", "Cria uma enquete"),
                ("!limpar [quantidade]", "Limpa mensagens (mod only)"),
                ("!avatar [@usuário]", "Mostra o avatar"),
                ("!tempo", "Horário atual")
            ]
            
            for command, description in basic_commands:
                embed.add_field(name=command, value=description, inline=False)
            
            # Comandos OCR (se disponível)
            if self.ocr:
                embed.add_field(name="📝 **COMANDOS OCR**", value="Extração de texto de imagens", inline=False)
                ocr_commands = [
                    ("!ocr", "Extrai texto de imagem anexada"),
                    ("!ocr_url <link>", "Extrai texto de imagem via URL"),
                    ("!ocr_status", "Status do serviço OCR")
                ]
                
                for command, description in ocr_commands:
                    embed.add_field(name=command, value=description, inline=False)
            
            embed.add_field(name="!ajuda", value="Mostra esta mensagem", inline=False)
            embed.set_footer(text="Use ! antes de cada comando")
            await ctx.send(embed=embed)
    
    def run(self):
        """Inicia o bot"""
        # Configurar comando de ajuda atualizado
        self.setup_help_command()
        
        token = os.getenv('DISCORD_TOKEN')
        if token:
            print("🚀 Iniciando o bot...")
            self.bot.run(token)
        else:
            print("❌ ERRO: Token do Discord não encontrado!")
            print("Crie um arquivo .env com:")
            print("DISCORD_TOKEN=seu_token_aqui")
            print("GOOGLE_CREDENTIALS_PATH=caminho/para/credentials.json")

