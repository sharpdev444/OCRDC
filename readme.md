# 🤖 Discord Bot com Integração OCR (Google Cloud Vision)

Um bot para Discord multifuncional escrito em Python, que utiliza a **Google Cloud Vision API** para realizar **extração de texto de imagens (OCR)** e oferece diversos comandos úteis e de moderação. O bot pode processar imagens enviadas diretamente no chat ou via URL, além de possuir uma funcionalidade específica para identificar "códigos de apoiador" em imagens.

---

## ✨ Funcionalidades Principais

### 🤖 Funcionalidades do Bot Discord:
-   **Comandos Gerais:**
    -   `!ping`: Verifica a latência do bot.
    -   `!moeda`: Joga uma moeda (cara ou coroa).
    -   `!avatar [@usuário]`: Exibe o avatar de um usuário (ou o seu, se nenhum usuário for mencionado).
    -   `!ajuda`: Mostra uma lista de todos os comandos disponíveis.
-   **Comandos de Moderação:**
    -   `!limpar [quantidade]`: Apaga um número especificado de mensagens do canal (requer permissão de gerenciamento de mensagens).
-   **Tratamento de Erros:** Respostas amigáveis para comandos não encontrados ou falta de permissão.
-   **Status Personalizado:** Exibe "Digite !ajuda" como status do bot.

### 📷 Funcionalidades de OCR (Integrado ao Bot):
-   **Extração de Texto de Imagens Anexadas:**
    -   `!ocr`: Processa uma imagem anexada à mensagem, realiza um pré-processamento para otimizar a leitura e extrai o texto.
    -   `!ocr_quality`: Processa uma imagem anexada à mensagem e extrai o texto, priorizando a qualidade da extração (sem pré-processamento agressivo).
-   **Extração de Texto de Imagens via URL:**
    -   `!ocr_url <link_da_imagem>`: Baixa uma imagem de uma URL fornecida e extrai o texto.
-   **Detecção de Código de Apoiador:**
    -   `!apoiador`: Analisa uma imagem anexada para encontrar a frase "APOIE-UM-CRIADOR" (ou variações em inglês) seguida do código específico "Vascurado". A imagem passa por um pré-processamento para melhorar a detecção.
-   **Status do Serviço de OCR:**
    -   `!ocr_status`: Verifica e informa o estado atual do serviço de OCR (se está configurado e operacional).
-   **Pré-processamento de Imagem:** Para os comandos `!ocr` e `!apoiador`, as imagens são pré-processadas (convertidas para escala de cinza, nitidez aumentada, binarização adaptativa e redimensionamento) para melhorar a velocidade e precisão do OCR.
-   **Feedback ao Usuário:** Mensagens de "processando", resultados formatados, estatísticas do texto extraído (quantidade de caracteres, palavras) e envio do texto completo como arquivo `.txt` caso exceda o limite de caracteres do Discord.

### ⚙️ Funcionalidades do Motor OCR (Google Cloud Vision - `ocr.py`):
-   🖼️ **Processamento de imagens remotas:** Download e OCR de imagens diretamente via URL.
-   📁 **Processamento de imagens locais:** OCR de arquivos de imagem armazenados no sistema de arquivos (usado para testes e pela biblioteca).
-   🔄 **Sistema de retry com backoff exponencial:** Requisições falhas à API Vision são automaticamente reprocessadas com intervalos progressivos.
-   📝 **Logging detalhado:** Informações completas de execução para facilitar debugging e monitoramento, salvas em `ocr_script.log`.
-   ⚡ **Tratamento robusto de erros:** Captura e tratamento de exceções específicas da Google Vision API.

---

## 📦 Pré-requisitos

-   [x] Python **3.7+**
-   [x] Conta no **Google Cloud Platform** com a **Vision API** habilitada.
-   [x] Arquivo de credenciais de autenticação do Google Cloud:
    -   JSON (chave de conta de serviço).
    -   Alternativamente, **ADC** (Application Default Credentials) configurado no ambiente onde o bot será executado.
-   [x] **Token do Bot Discord**.
-   [x] Bibliotecas Python:
    -   `discord.py`
    -   `google-cloud-vision`
    -   `python-dotenv`
    -   `requests`
    -   `aiohttp`
    -   `opencv-python` (cv2)
    -   `numpy`

---

## 🔧 Configuração e Instalação

1.  **Clone o repositório:**
    ```bash
    git clone <url-do-seu-repositorio>
    cd <nome-do-diretorio-do-projeto>
    ```

2.  **Crie e ative um ambiente virtual (recomendado):**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    Crie um arquivo `requirements.txt` com o seguinte conteúdo:
    ```txt
    discord.py
    google-cloud-vision
    python-dotenv
    requests
    aiohttp
    opencv-python
    numpy
    ```
    E então instale-as:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as credenciais do Google Cloud:**
    -   Coloque o seu arquivo JSON de credenciais do Google Cloud no projeto (por exemplo, na raiz ou em um diretório `config`).
    -   **OU** configure as `Application Default Credentials` seguindo a documentação do Google Cloud.

5.  **Configure as variáveis de ambiente:**
    -   Crie um diretório chamado `config` na raiz do projeto, se ainda não existir.
    -   Dentro do diretório `config`, crie um arquivo chamado `.env`.
    -   Adicione as seguintes variáveis ao arquivo `.env`, substituindo pelos seus valores:
        ```env
        DISCORD_TOKEN=SEU_TOKEN_DO_BOT_DISCORD_AQUI
        GOOGLE_CREDENTIALS_PATH=CAMINHO_PARA_SEU_ARQUIVO_DE_CREDENCIAS.json
        ```
        Exemplo de `GOOGLE_CREDENTIALS_PATH`: Se o arquivo `googleAPI_key.json` estiver na raiz do projeto, o caminho será `googleAPI_key.json`. Se estiver dentro de uma pasta `config`, será `config/googleAPI_key.json`.

---

## 🚀 Como Executar

1.  Certifique-se de que todas as configurações (passo 🔧) foram concluídas.
2.  Execute o arquivo `main.py`:
    ```bash
    python main.py
    ```
3.  O terminal deverá indicar que o bot está online e o serviço de OCR (se configurado corretamente). O bot estará pronto para responder aos comandos no Discord.
    -   Por padrão, o `main.py` está configurado para iniciar o bot Discord (`teste = "discord"`). Para testar apenas a funcionalidade OCR com uma URL de exemplo (conforme o código em `main.py`), você pode alterar a variável `teste` para `"googleOCR"` no arquivo `main.py` e executar novamente.

---

## 📋 Comandos do Bot

Uma vez que o bot esteja online no seu servidor Discord:

**Comandos Gerais:**
-   `!ping`: Mostra a latência do bot.
-   `!moeda`: Cara ou Coroa?
-   `!avatar`: Mostra seu avatar.
-   `!avatar @membro`: Mostra o avatar do membro mencionado.
-   `!ajuda`: Exibe a mensagem de ajuda com todos os comandos.

**Comandos de OCR:**
-   `!ocr` (com uma imagem anexada): Extrai texto da imagem anexada (com pré-processamento).
-   `!ocr_quality` (com uma imagem anexada): Extrai texto da imagem anexada (foco na qualidade, sem pré-processamento agressivo).
-   `!ocr_url <link_da_imagem>`: Extrai texto de uma imagem a partir de um link.
-   `!apoiador` (com uma imagem anexada): Verifica se a imagem contém o código de apoiador "Vascurado" e a frase "APOIE-UM-CRIADOR" (ou variações).
-   `!ocr_status`: Mostra o status do serviço de OCR.

**Comandos de Moderação:**
-   `!limpar <número>`: Apaga o número especificado de mensagens (padrão: 5). Ex: `!limpar 10`.

---

## 📁 Estrutura do Projeto (Simplificada)
