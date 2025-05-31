from ocr import GoogleOCR

if __name__ == "__main__":
    credentials_path = r"googleAPI_key.json"
    ocr_client = GoogleOCR(credentials_path)  
    
    try:
        image_url = "https://cdn.discordapp.com/attachments/976244546902040596/1374825370020216882/Imagem_do_WhatsApp_de_2025-05-21_as_16.04.19_191d31ef.jpg?ex=683ca467&is=683b52e7&hm=60e12019e2bf6960fe412bc96af3c92f1267ba66be4ddefe30d928c0ba939403&"
        
        ocr_client.process_image_url(image_url)  
        
    except Exception as e:
        print(f"Error: {e}")