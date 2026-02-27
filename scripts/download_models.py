import os
import logging
from sentence_transformers import SentenceTransformer
from transformers import pipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_models():
    """
    Pre-downloads models during Docker build to bake them into the image.
    relies on HF_HOME environment variable to store them.
    """
    logger.info("Starting model download...")
    
    # 1. Sentence Transformer for Embeddings
    logger.info("Downloading SentenceTransformer: all-MiniLM-L6-v2")
    SentenceTransformer("all-MiniLM-L6-v2")
    
    # 2. QA Pipeline Model
    logger.info("Downloading QA Model: distilbert-base-cased-distilled-squad")
    pipeline("question-answering", model="distilbert-base-cased-distilled-squad")
    
    logger.info("✅ Models successfully downloaded and cached.")

if __name__ == "__main__":
    download_models()
