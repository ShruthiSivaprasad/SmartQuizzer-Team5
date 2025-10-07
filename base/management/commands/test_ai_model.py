from django.core.management.base import BaseCommand
from base.models import Profile
from base.ai import MLSuggestionEngine


class Command(BaseCommand):
    help = 'Test the AI suggestion model'

    def handle(self, *args, **options):
        self.stdout.write("Testing AI Suggestion Model...")
        
        # Initialize the ML engine
        engine = MLSuggestionEngine()
        
        if engine.is_trained:
            self.stdout.write(self.style.SUCCESS("✓ Model is trained and ready"))
        else:
            self.stdout.write(self.style.ERROR("✗ Model training failed"))
            return
        
        # Test with a sample user (if any exist)
        users = Profile.objects.all()[:3]
        
        if not users:
            self.stdout.write(self.style.WARNING("No users found to test with"))
            return
        
        for user in users:
            self.stdout.write(f"\n--- Testing with user: {user.username} ---")
            
            try:
                suggestion = engine.recommend(user)
                self.stdout.write(f"Suggestion: {suggestion.text}")
                self.stdout.write(f"Topic: {suggestion.topic}")
                self.stdout.write(f"Difficulty: {suggestion.recommended_difficulty}")
                self.stdout.write(f"Rationale: {suggestion.rationale}")
                
                if 'confidence' in suggestion.stats:
                    self.stdout.write(f"ML Confidence: {suggestion.stats['confidence']:.1f}%")
                
                if 'model_prediction' in suggestion.stats:
                    self.stdout.write(f"Model Prediction: {suggestion.stats['model_prediction']}")
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error testing user {user.username}: {e}"))
        
        self.stdout.write(self.style.SUCCESS("\nAI Model test completed!"))
