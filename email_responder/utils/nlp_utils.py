import nltk
import spacy
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download required NLTK data with robust error handling
def _download_nltk_resources():
    resources = {
        'punkt': 'tokenizers/punkt',
        'stopwords': 'corpora/stopwords',
        'wordnet': 'corpora/wordnet',  # For lemmatization
        'averaged_perceptron_tagger': 'taggers/averaged_perceptron_tagger'
    }
    
    for resource, path in resources.items():
        try:
            nltk.data.find(path)
        except LookupError:
            try:
                nltk.download(resource, quiet=True)
                logger.info(f"Successfully downloaded NLTK {resource} data")
            except Exception as e:
                logger.error(f"Failed to download NLTK {resource}: {str(e)}")
                if resource == 'punkt':  # Critical for tokenization
                    raise

# Initialize NLTK resources
_download_nltk_resources()

# Load spaCy model with fallback
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("spaCy model not found, downloading...")
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

# Initialize stopwords
stop_words = set(stopwords.words('english'))
extra_stopwords = {'http', 'https', 'www', 'com', 'subject'}  # Add custom stopwords
stop_words.update(extra_stopwords)

def preprocess_text(text):
    """Enhanced text preprocessing with error handling"""
    if not isinstance(text, str) or not text.strip():
        return ""
    
    try:
        # Normalize text
        text = text.lower().strip()
        
        # Remove email headers and signatures
        if "-----Original Message-----" in text:
            text = text.split("-----Original Message-----")[0]
        if "--\n" in text:
            text = text.split("--\n")[0]
            
        # Remove punctuation and numbers
        text = text.translate(str.maketrans('', '', string.punctuation + string.digits))
        
        # Tokenize with NLTK
        tokens = word_tokenize(text)
        
        # Filter tokens
        filtered_tokens = [
            word for word in tokens 
            if (word not in stop_words and 
                len(word) > 2 and 
                word.isalpha())
        ]
        
        # Lemmatization with spaCy
        doc = nlp(" ".join(filtered_tokens))
        lemmas = [token.lemma_ for token in doc]
        
        return " ".join(lemmas)
        
    except Exception as e:
        logger.error(f"Error preprocessing text: {str(e)}")
        return ""  # Return empty string on failure