import os
import logging
import requests
from google.cloud import vision
from google.api_core import exceptions
import time
from typing import Optional, List


class GoogleOCR:
    
    def __init__(self, credentials_path: str):
        self._setup_logging()
        self.client = None
        
        if credentials_path:
            self.setup_credentials(credentials_path)

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('ocr_script.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_credentials(self, credentials_path: str):
        if not os.path.exists(credentials_path):
            self.logger.error(f"Credentials file not found: {credentials_path}")
            raise FileNotFoundError(f"Google Cloud credentials file not found: {credentials_path}")

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        
        try:
            self.client = vision.ImageAnnotatorClient()
            self.logger.info("Google Cloud credentials configured successfully.")
        except Exception as e:
            self.logger.error(f"Failed to initialize Vision API client: {e}")
            raise

    def download_image(self, url: str, timeout: int = 30) -> bytes:
        try:
            self.logger.info(f"Downloading image")

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = requests.get(url, headers=headers, timeout=timeout, stream=True)
            response.raise_for_status()

            image_content = b''
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    image_content += chunk

            if not image_content:
                self.logger.error("Downloaded image is empty.")
                raise ValueError("Downloaded image is empty.")

            content_type = response.headers.get('content-type', '').lower()
            if content_type and 'image' not in content_type:
                self.logger.warning(f"Content type '{content_type}' may not be an image")

            if len(image_content) > 20 * 1024 * 1024:
                self.logger.warning(f"Image size ({len(image_content)} bytes) may exceed Vision API limits")

            self.logger.info(f"Image downloaded successfully. Size: {len(image_content)} bytes")
            return image_content

        except requests.exceptions.Timeout:
            self.logger.error(f"Request timed out after {timeout} seconds for URL: {url}")
            raise
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error for URL: {url} - {e}")
            raise
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error {e.response.status_code} for URL: {url}")
            if e.response.status_code == 404:
                self.logger.error("Image not found (404) - URL may be incorrect or expired.")
            raise
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for URL {url}: {e}")
            raise

    def perform_ocr(self, image_bytes: bytes, max_retries: int = 3) -> Optional[List]:
        if not self.client:
            self.logger.error("Vision API client not initialized. Call setup_credentials first.")
            raise RuntimeError("Vision API client not initialized. Ensure credentials are set up.")

        image = vision.Image(content=image_bytes)

        for attempt in range(max_retries):
            try:
                self.logger.info(f"Performing OCR (attempt {attempt + 1}/{max_retries})")
                response = self.client.text_detection(image=image)

                if response.error.message:
                    error_msg = response.error.message
                    self.logger.error(f"Vision API error: {error_msg}")
                    
                    if any(phrase in error_msg.lower() for phrase in ["bad image", "invalid image", "unsupported"]):
                        raise exceptions.InvalidArgument(f"Invalid image data: {error_msg}")
                    
                    raise exceptions.GoogleAPIError(f"Vision API error: {error_msg}")

                self.logger.info("OCR completed successfully")
                return response.text_annotations

            except exceptions.ResourceExhausted as e:
                self.logger.warning(f"Vision API quota exceeded: {e}")
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + (time.time() % 1)
                    self.logger.info(f"Retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                else:
                    self.logger.error("Max retries reached for quota exceeded error.")
                    raise

            except exceptions.ServiceUnavailable as e:
                self.logger.warning(f"Vision API service unavailable: {e}")
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + (time.time() % 1)
                    self.logger.info(f"Retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                else:
                    self.logger.error("Max retries reached for service unavailable error.")
                    raise

            except exceptions.InvalidArgument as e:
                self.logger.error(f"Invalid argument error: {e}")
                self.logger.error("This usually means the image is corrupted, invalid format, or too large.")
                raise

            except exceptions.GoogleAPIError as e:
                self.logger.error(f"Google API error during OCR attempt {attempt + 1}: {e}")
                
                error_str = str(e).lower()
                if any(phrase in error_str for phrase in ["customer care", "service client", "account"]):
                    self.logger.error("Non-retryable API error encountered.")
                    raise
                
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + (time.time() % 1)
                    self.logger.info(f"Retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                else:
                    self.logger.error("Max retries reached for Google API error.")
                    raise

        return None

    def process_results(self, texts: Optional[List]) -> str:
        if not texts:
            self.logger.info("No text detected in the image")
            print("No text detected.")
            return ""

        self.logger.info(f"Found {len(texts)} text annotations")

        full_text = texts[0].description
        self.logger.info(f"Extracted text length: {len(full_text)} characters")

        print("=" * 50)
        print("EXTRACTED TEXT:")
        print("=" * 50)
        print(full_text)
        print("=" * 50)

        if len(texts) > 1:
            self.logger.debug("Individual text elements:")
            for i, text in enumerate(texts[1:], 1):
                self.logger.debug(f"Element {i}: '{text.description.strip()}'")

        return full_text

    def process_image_url(self, image_url: str, credentials_path: Optional[str] = None) -> str:
        try:
            self.logger.info(f"Starting OCR pipeline")
            
            if credentials_path:
                self.setup_credentials(credentials_path)
            
            if not self.client:
                raise RuntimeError("Vision API client not initialized. Provide credentials_path or call setup_credentials().")
            
            image_bytes = self.download_image(image_url)
            texts = self.perform_ocr(image_bytes)
            extracted_text = self.process_results(texts)
            
            self.logger.info("OCR pipeline completed successfully")
            return extracted_text
            
        except Exception as e:
            self.logger.error(f"OCR pipeline failed: {e}")
            raise

    def process_local_image(self, image_path: str) -> str:
        try:
            self.logger.info(f"Processing local image: {image_path}")
            
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            with open(image_path, 'rb') as image_file:
                image_bytes = image_file.read()
            
            texts = self.perform_ocr(image_bytes)
            extracted_text = self.process_results(texts)
            
            self.logger.info("Local image processing completed successfully")
            return extracted_text
            
        except Exception as e:
            self.logger.error(f"Local image processing failed: {e}")
            raise