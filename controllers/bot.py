import discord
from discord.ext import commands
import asyncio
import random
import os
import aiohttp
import io
import cv2
import numpy as np
from dotenv import load_dotenv

try:
    from controllers.ocr import GoogleOCR
    OCR_AVAILABLE = True
except ImportError:
    print("⚠️ GoogleOCR não disponível. Comandos de OCR serão desabilitados.")
    OCR_AVAILABLE = False

class ApoiadorBot:
    def __init__(self):

        env_path = "./config/.env"
        load_dotenv(dotenv_path=env_path)
                
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
            await self.bot.change_presence(activity=discord.Game(name=status_text))
        
        
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

    
    def setup_ocr_commands(self):
        """Configura comandos relacionados ao OCR"""
        
        @self.bot.command(name='ocr')
        async def ocr_command(ctx):
            """Extrai texto de uma imagem anexada ou URL"""
            if not self.ocr:
                embed = discord.Embed(
                    title=" ❌ Serviço de OCR Indisponivel",
                    description="Serviço em Manutenção Temporaria",
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
                            
                    #Processar Imagem pra diminuir o tempo
                    def preprocess_image(image_bytes):
                        # Convert bytes to numpy array
                        nparr = np.frombuffer(image_bytes, np.uint8)
                        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                        # Convert to grayscale
                        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                        # Sharpen the image
                        blurred = cv2.GaussianBlur(gray, (0, 0), 3)
                        sharpened = cv2.addWeighted(gray, 1.5, blurred, -0.5, 0)

                        # Adaptive threshold for better text separation
                        thresh = cv2.adaptiveThreshold(
                            sharpened, 255,
                            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                            cv2.THRESH_BINARY,
                            11, 2
                        )

                        # Resize if necessary
                        max_height = 1024
                        height, width = thresh.shape
                        if height > max_height:
                            scale = max_height / height
                            thresh = cv2.resize(thresh, (int(width * scale), max_height))

                        # Encode to bytes
                        is_success, buffer = cv2.imencode(".jpg", thresh)
                        if is_success:
                            return buffer.tobytes()
                    
                    image_data = preprocess_image(image_data)
                    
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

        @self.bot.command(name='ocr_quality')
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
        
        @self.bot.command(name='apoiador')
        async def apoiador_command(ctx):
            """Check if in the image there is an instance of 'codigo de apoiador' and their respective code"""

            if not self.ocr:
                embed = discord.Embed(
                    title="❌ Serviço de Apoiador Automático Indisponível",
                    description="Serviço em Manutenção Temporária",
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
                    description="Analisando a imagem em busca do código de apoiador...",
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
                            
                    #Processar Imagem pra diminuir o tempo
                    def preprocess_image(image_bytes):
                        # Convert bytes to numpy array
                        nparr = np.frombuffer(image_bytes, np.uint8)
                        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                        # Convert to grayscale
                        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                        # Sharpen the image
                        blurred = cv2.GaussianBlur(gray, (0, 0), 3)
                        sharpened = cv2.addWeighted(gray, 1.5, blurred, -0.5, 0)

                        # Adaptive threshold for better text separation
                        thresh = cv2.adaptiveThreshold(
                            sharpened, 255,
                            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                            cv2.THRESH_BINARY,
                            11, 2
                        )

                        # Resize if necessary
                        max_height = 1024
                        height, width = thresh.shape
                        if height > max_height:
                            scale = max_height / height
                            thresh = cv2.resize(thresh, (int(width * scale), max_height))

                        # Encode to bytes
                        is_success, buffer = cv2.imencode(".jpg", thresh)
                        if is_success:
                            return buffer.tobytes()
                    
                    image_data = preprocess_image(image_data)
                    # Processar OCR
                    texts = self.ocr.perform_ocr(image_data)
                    
                    if texts and len(texts) > 0:
                        extracted_text = texts[0].description.lower()  # Converter para minúsculas para busca
                        
                        # Definir os códigos e textos a procurar

                        target_code = 'Vascurado'
                        target_phrases = [f"APOIE-UM-CRIADOR: {target_code}",f"Support-a-Creator: {target_code}",f"SUPPORT-A-CREATOR: {target_code}"]

                        flag = False
                        for phrase in target_phrases:
                            if phrase.lower() in extracted_text or target_code.lower in extracted_text:
                                flag = True
                                break
                        if flag:
                            # Sucesso - encontrou ambos
                            success_embed = discord.Embed(
                                title="✅ Código de Apoiador Encontrado!",
                                description=f"**Código detectado:** {target_code.upper()}",
                                color=0x32CD32
                            )
                            success_embed.add_field(
                                name="📋 Status", 
                                value="Código de apoiador válido confirmado!", 
                                inline=False
                            )
                            success_embed.set_footer(text=f"Verificado por {ctx.author.display_name}")
                            await processing_msg.edit(embed=success_embed)
                            
                            
                        else:
                            # Não encontrou "codigo de apoiador"
                            not_found_embed = discord.Embed(
                                title="❌ Código de Apoiador Não Encontrado",
                                description="Não foi possível encontrar o Código de Apoiador na imagem",
                                color=0xff0000
                            )
                            not_found_embed.add_field(
                                name="💡 Dica", 
                                value="Certifique-se de que a imagem contém o texto 'Código de Apoiador' de forma legível.", 
                                inline=False
                            )
                            await processing_msg.edit(embed=not_found_embed)
                    
                    else:
                        # Nenhum texto foi detectado
                        no_text_embed = discord.Embed(
                            title="❌ Nenhum Texto Detectado",
                            description="Não foi possível detectar texto na imagem.",
                            color=0xff0000
                        )
                        no_text_embed.add_field(
                            name="💡 Sugestões",
                            value="• Verifique se a imagem está nítida\n• Certifique-se de que há texto visível\n• Tente uma imagem com melhor qualidade",
                            inline=False
                        )
                        await processing_msg.edit(embed=no_text_embed)
                        
                except Exception as e:
                    error_embed = discord.Embed(
                        title="❌ Erro no Processamento",
                        description=f"Ocorreu um erro ao processar a imagem.",
                        color=0xff0000
                    )
                    error_embed.add_field(
                        name="🔧 Detalhes do Erro", 
                        value=f"```{str(e)}```", 
                        inline=False
                    )
                    await processing_msg.edit(embed=error_embed)
                    print(f"Erro no comando apoiador: {e}")  # Log para debug
                    
            else:
                embed = discord.Embed(
                    title="📷 Como usar o comando Apoiador",
                    description="Este comando verifica se há um código de apoiador válido na imagem.",
                    color=0x0099ff
                )
                embed.add_field(
                    name="📤 Anexar Imagem",
                    value="Envie o comando `!apoiador` junto com a foto anexada",
                    inline=False
                )
                embed.add_field(
                    name="🎯 O que procura",
                    value="• Texto 'Código de Apoiador'\n• Código específico: 'Vascurado'",
                    inline=False
                )
                embed.add_field(
                    name="📋 Formatos Suportados",
                    value="PNG, JPG, JPEG, GIF, BMP, WEBP",
                    inline=False
                )
                await ctx.send(embed=embed)
                            
        
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

