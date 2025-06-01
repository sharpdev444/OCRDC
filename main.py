from ocr import GoogleOCR
from bot import ApoiadorBot

if __name__ == "__main__":
    credentials_path = r"googleAPI_key.json"

    teste = "discord"  

    if teste == "googleOCR":
        ocr_client = GoogleOCR(credentials_path)
        try:
            image_url = "https://cdn.discordapp.com/attachments/976244546902040596/1378516116124467251/image.png?ex=683ce2ad&is=683b912d&hm=ac895fe73d3d727e1d34e5a0aeaac3cd64d1a89795d00c8f2ec870783b06f0b2&"
            ocr_client.process_image_url(image_url)  
            
        except Exception as e:
            print(f"Error: {e}")
    elif teste == "discord":
        bot = ApoiadorBot()
        bot.run()

    
