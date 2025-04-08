import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

class EmailClassifier:
    def __init__(self, model_path='models/email_classifier.joblib'):
        """Initialize with the path where the model is saved."""
        self.model_path = model_path
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        self.model = self._load_model()

    def _load_model(self):
        """Load the model from disk if it exists, else initialize a new model."""
        if os.path.exists(self.model_path):
            print("🔄 Loading existing model...")
            try:
                return joblib.load(self.model_path)
            except Exception as e:
                print(f"❌ Error loading model: {e}")
                return self._initialize_new_model()
        else:
            print("🆕 No model found, initializing a new one...")
            return self._initialize_new_model()

    def _initialize_new_model(self):
        """Initialize a new model."""
        return Pipeline([
            ('tfidf', TfidfVectorizer()),
            ('clf', MultinomialNB())
        ])

    def train(self, texts, labels):
        """Train with sample data and save the model."""
        print("🤖 Training classifier...")
        self.model.fit(texts, labels)
        try:
            joblib.dump(self.model, self.model_path)
            print(f"✅ Model trained and saved to {self.model_path}")
        except Exception as e:
            print(f"❌ Error saving model: {e}")

    def predict(self, text):
        """Predict email category."""
        return self.model.predict([text])[0]

    def evaluate(self, texts, labels):
        """Evaluate the model with test data."""
        from sklearn.metrics import accuracy_score, classification_report
        predictions = self.model.predict(texts)
        accuracy = accuracy_score(labels, predictions)
        report = classification_report(labels, predictions)
        print(f"Accuracy: {accuracy:.4f}")
        print("Classification Report:\n", report)

