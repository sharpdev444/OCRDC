# 📷 Google Cloud Vision OCR

Um cliente Python para **extração de texto de imagens** usando a **Google Cloud Vision API**.

---

## ✨ Funcionalidades

- 🖼️ **Processamento de imagens remotas**  
  Download e OCR de imagens diretamente via URL.

- 📁 **Processamento de imagens locais**  
  OCR de arquivos de imagem armazenados no sistema de arquivos.

- 🔄 **Sistema de retry com backoff exponencial**  
  Requisições falhas são automaticamente reprocessadas com intervalos progressivos.

- 📝 **Logging detalhado**  
  Informações completas de execução para facilitar debugging e monitoramento.

- ⚡ **Tratamento robusto de erros**  
  Captura e tratamento de exceções específicas da Google Vision API.

---

## 📦 Pré-requisitos

- [x] Python **3.7+**
- [x] Conta no **Google Cloud Platform** com a **Vision API** habilitada
- [x] Arquivo de credenciais de autenticação:
  - JSON (chave de conta de serviço)
  - ou **ADC** (Application Default Credentials)

---


