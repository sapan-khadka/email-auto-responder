from transformers import pipeline, set_seed
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResponseGenerator:
    def __init__(self):
        """Initialize the response generator with GPT-2"""
        logger.info("💡 Loading response generator...")
        set_seed(42)  # For reproducibility
        
        try:
            self.generator = pipeline(
                "text-generation",
                model="gpt2",
                device=-1,  # Change to 0 if you have GPU available
                framework="pt",  # Explicitly use PyTorch
                tokenizer="gpt2"
            )
            logger.info("Response generator loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load response generator: {str(e)}")
            raise

    def generate_response(self, email_text):
        """Generate a professional email response"""
        if not email_text or not isinstance(email_text, str):
            return "Thank you for your email. I'll get back to you soon."
        
        try:
            prompt = (
                "You are a professional email assistant. Respond to this email in a polite and concise manner:\n\n"
                f"Original email:\n{email_text}\n\n"
                "Professional response:"
            )
            
            # Generate the response using the model
            response = self.generator(
                prompt,
                max_length=150,
                num_return_sequences=1,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.1,
                do_sample=True,
                truncation=True,
                pad_token_id=self.generator.tokenizer.eos_token_id
            )
            
            # Extract just the generated response
            full_text = response[0]['generated_text']
            response_text = full_text.split("Professional response:")[-1].strip()

            # If the split didn't work properly (edge cases), just return what the model generated
            if not response_text:
                response_text = full_text.strip()

            return response_text
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "Thank you for your email. I'll get back to you soon."
