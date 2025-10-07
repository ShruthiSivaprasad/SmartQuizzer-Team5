from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
import pickle
import os
from django.db.models import Count, Avg, Max  # pyright: ignore[reportAttributeAccessIssue]
from .models import QuizResult, Profile
from ui.models import MCQ


@dataclass
class AISuggestion:
    text: str
    topic: Optional[str]
    recommended_difficulty: Optional[str]
    rationale: str
    stats: Dict[str, Any]
    priority: int = 1  # 1=primary, 2=secondary, 3=alternative

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "topic": self.topic,
            "recommended_difficulty": self.recommended_difficulty,
            "rationale": self.rationale,
            "stats": self.stats,
            "priority": self.priority,
        }


class MLSuggestionEngine:
    """
    Machine Learning-based AI engine using Decision Tree Classifier for next-step recommendations.
    
    Features used for prediction:
    - Easy attempts count, Easy average score
    - Medium attempts count, Medium average score  
    - Hard attempts count, Hard average score
    - Overall quiz count, Overall average score
    - Days since first quiz, Days since last quiz
    
    Predicts: next_action (0=Easy, 1=Medium, 2=Hard, 3=NextTopic)
    """
    
    def __init__(self):
        self.model = DecisionTreeClassifier(
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        self.difficulty_encoder = LabelEncoder()
        self.action_encoder = LabelEncoder()
        self.is_trained = False
        self.model_path = os.path.join(os.path.dirname(__file__), 'suggestion_model.pkl')
        self._load_or_train_model()

    def _get_focus_topic(self, user: Profile) -> Optional[str]:
        # Determine the user's focus topic by most attempts overall
        agg = (
            QuizResult.objects.filter(user=user)
            .values("topic")
            .annotate(quiz_count=Count("id"))
            .order_by("-quiz_count")
        )
        return agg[0]["topic"] if agg else None

    def _extract_features(self, user: Profile, topic: str) -> np.ndarray:
        """Extract ML features for the user's performance on a specific topic"""
        from datetime import datetime
        from django.utils import timezone
        
        # Get difficulty-specific stats
        by_diff = (
            QuizResult.objects.filter(user=user, topic=topic)
            .values("difficulty_level")
            .annotate(
                cnt=Count("id"),
                avg=Avg("score_percentage"),
            )
        )
        
        stats = {"Easy": {"count": 0, "avg": 0.0}, "Medium": {"count": 0, "avg": 0.0}, "Hard": {"count": 0, "avg": 0.0}}
        for row in by_diff:
            diff = row["difficulty_level"]
            if diff in stats:
                stats[diff] = {"count": int(row["cnt"] or 0), "avg": float(row["avg"] or 0.0)}
        
        # Overall stats for this topic
        all_results = QuizResult.objects.filter(user=user, topic=topic).order_by('date_taken')
        total_quizzes = all_results.count()
        overall_avg = all_results.aggregate(avg=Avg('score_percentage'))['avg'] or 0.0
        
        # Time-based features
        days_since_first = 0
        days_since_last = 0
        if total_quizzes > 0:
            first_quiz = all_results.first().date_taken
            last_quiz = all_results.last().date_taken
            now = timezone.now()
            days_since_first = (now - first_quiz).days
            days_since_last = (now - last_quiz).days
        
        # Feature vector: [easy_count, easy_avg, medium_count, medium_avg, hard_count, hard_avg, 
        #                  total_quizzes, overall_avg, days_since_first, days_since_last]
        features = np.array([
            stats["Easy"]["count"], stats["Easy"]["avg"],
            stats["Medium"]["count"], stats["Medium"]["avg"], 
            stats["Hard"]["count"], stats["Hard"]["avg"],
            total_quizzes, overall_avg,
            days_since_first, days_since_last
        ]).reshape(1, -1)
        
        return features

    def _find_next_topic(self, current_topic: str) -> Optional[str]:
        # Suggest another topic: choose a topic with the fewest attempts, or any different topic if no history.
        topics = list(
            MCQ.objects.values_list("topic", flat=True).distinct().order_by("topic")
        )
        topics = [t for t in topics if t and t != current_topic]
        return topics[0] if topics else None

    def _generate_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Generate synthetic training data based on the original rules"""
        X_train = []
        y_train = []
        
        # Generate synthetic data points based on the original rule logic
        # This creates a dataset that the ML model can learn from
        
        # Rule 1: Easy mastery -> Medium (easy_count >= 5, easy_avg > 80)
        for _ in range(50):
            easy_count = np.random.randint(5, 15)
            easy_avg = np.random.uniform(80, 95)
            medium_count = np.random.randint(0, 3)
            medium_avg = np.random.uniform(50, 80)
            hard_count = np.random.randint(0, 2)
            hard_avg = np.random.uniform(40, 70)
            total_quizzes = easy_count + medium_count + hard_count
            overall_avg = (easy_count * easy_avg + medium_count * medium_avg + hard_count * hard_avg) / total_quizzes
            days_since_first = np.random.randint(7, 60)
            days_since_last = np.random.randint(0, 7)
            
            X_train.append([easy_count, easy_avg, medium_count, medium_avg, hard_count, hard_avg, 
                           total_quizzes, overall_avg, days_since_first, days_since_last])
            y_train.append(1)  # Suggest Medium
        
        # Rule 2: Medium mastery -> Hard (medium_count >= 5, medium_avg > 75)
        for _ in range(50):
            easy_count = np.random.randint(5, 15)
            easy_avg = np.random.uniform(80, 95)
            medium_count = np.random.randint(5, 12)
            medium_avg = np.random.uniform(75, 90)
            hard_count = np.random.randint(0, 3)
            hard_avg = np.random.uniform(50, 75)
            total_quizzes = easy_count + medium_count + hard_count
            overall_avg = (easy_count * easy_avg + medium_count * medium_avg + hard_count * hard_avg) / total_quizzes
            days_since_first = np.random.randint(14, 90)
            days_since_last = np.random.randint(0, 7)
            
            X_train.append([easy_count, easy_avg, medium_count, medium_avg, hard_count, hard_avg,
                           total_quizzes, overall_avg, days_since_first, days_since_last])
            y_train.append(2)  # Suggest Hard
        
        # Rule 3: Hard mastery -> Next Topic (hard_count >= 3, hard_avg > 80)
        for _ in range(30):
            easy_count = np.random.randint(5, 15)
            easy_avg = np.random.uniform(80, 95)
            medium_count = np.random.randint(5, 12)
            medium_avg = np.random.uniform(75, 90)
            hard_count = np.random.randint(3, 8)
            hard_avg = np.random.uniform(80, 95)
            total_quizzes = easy_count + medium_count + hard_count
            overall_avg = (easy_count * easy_avg + medium_count * medium_avg + hard_count * hard_avg) / total_quizzes
            days_since_first = np.random.randint(21, 120)
            days_since_last = np.random.randint(0, 7)
            
            X_train.append([easy_count, easy_avg, medium_count, medium_avg, hard_count, hard_avg,
                           total_quizzes, overall_avg, days_since_first, days_since_last])
            y_train.append(3)  # Suggest Next Topic
        
        # Rule 4: Beginners -> Easy (low counts, mixed performance)
        for _ in range(70):
            easy_count = np.random.randint(0, 5)
            easy_avg = np.random.uniform(40, 85)
            medium_count = np.random.randint(0, 3)
            medium_avg = np.random.uniform(30, 70)
            hard_count = np.random.randint(0, 2)
            hard_avg = np.random.uniform(20, 60)
            total_quizzes = max(1, easy_count + medium_count + hard_count)
            overall_avg = (easy_count * easy_avg + medium_count * medium_avg + hard_count * hard_avg) / total_quizzes if total_quizzes > 0 else 50
            days_since_first = np.random.randint(1, 30)
            days_since_last = np.random.randint(0, 14)
            
            X_train.append([easy_count, easy_avg, medium_count, medium_avg, hard_count, hard_avg,
                           total_quizzes, overall_avg, days_since_first, days_since_last])
            y_train.append(0)  # Suggest Easy
        
        return np.array(X_train), np.array(y_train)

    def _load_or_train_model(self):
        """Load existing model or train a new one"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                    self.model = model_data['model']
                    self.action_encoder = model_data['action_encoder']
                    self.is_trained = True
                    return
            except Exception as e:
                print(f"Failed to load model: {e}")
        
        # Train new model
        self._train_model()

    def _train_model(self):
        """Train the Decision Tree model"""
        X_train, y_train = self._generate_training_data()
        
        # Fit the action encoder
        self.action_encoder.fit([0, 1, 2, 3])  # Easy, Medium, Hard, NextTopic
        
        # Train the model
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # Save the trained model
        try:
            model_data = {
                'model': self.model,
                'action_encoder': self.action_encoder
            }
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
        except Exception as e:
            print(f"Failed to save model: {e}")

    def get_multiple_suggestions(self, user: Profile, max_suggestions: int = 3) -> List[AISuggestion]:
        """Generate multiple AI suggestions for the user across different topics"""
        suggestions = []
        
        # Get quiz history
        any_quizzes = QuizResult.objects.filter(user=user)
        if not any_quizzes.exists():
            # For new users, suggest multiple topics at Easy level
            topics = list(MCQ.objects.values_list("topic", flat=True).distinct().order_by("topic")[:max_suggestions])
            for i, topic in enumerate(topics, start=1):
                suggestions.append(AISuggestion(
                    text=f"Start with '{topic}' at Easy level",
                    topic=topic,
                    recommended_difficulty="Easy",
                    rationale="Begin your learning journey with foundational questions",
                    stats={"alternative": True},
                    priority=i
                ))
            return suggestions[:max_suggestions]
        
        # Get all topics the user has attempted, sorted by most recent activity
        user_topics = (
            QuizResult.objects.filter(user=user)
            .values("topic")
            .annotate(
                quiz_count=Count("id"),
                latest_attempt=Max("date_taken")  # type: ignore
            )
            .order_by("-latest_attempt")
        )
        
        # Generate suggestions for each topic the user has attempted
        for topic_data in user_topics[:max_suggestions]:
            topic = topic_data["topic"]
            try:
                features = self._extract_features(user, topic)
                prediction = self.model.predict(features)[0]
                prediction_proba = self.model.predict_proba(features)[0]
                confidence = max(prediction_proba) * 100
                
                action_map = {0: "Easy", 1: "Medium", 2: "Hard", 3: "NextTopic"}
                predicted_action = action_map[prediction]
                
                if predicted_action == "NextTopic":
                    # User has mastered this topic, suggest a new one
                    next_topic = self._find_next_topic(topic)
                    if next_topic:
                        suggestions.append(AISuggestion(
                            text=f"You've mastered '{topic}'! Try '{next_topic}'",
                            topic=next_topic,
                            recommended_difficulty="Easy",
                            rationale="Based on your strong performance across all difficulty levels",
                            stats={"confidence": confidence, "previous_topic": topic},
                            priority=len(suggestions) + 1
                        ))
                    else:
                        # No new topic available, suggest continuing current topic at Hard
                        suggestions.append(AISuggestion(
                            text=f"Continue mastering '{topic}' at Hard level",
                            topic=topic,
                            recommended_difficulty="Hard",
                            rationale="Keep challenging yourself on this topic",
                            stats={"confidence": confidence},
                            priority=len(suggestions) + 1
                        ))
                else:
                    suggestions.append(AISuggestion(
                        text=f"Try {predicted_action} difficulty for '{topic}'",
                        topic=topic,
                        recommended_difficulty=predicted_action,
                        rationale="Based on your performance history and learning progress",
                        stats={"confidence": confidence},
                        priority=len(suggestions) + 1
                    ))
            except Exception as e:
                # If ML fails for this topic, skip it
                continue
        
        # If we don't have enough suggestions, add unexplored topics
        if len(suggestions) < max_suggestions:
            attempted_topics = set(t["topic"] for t in user_topics)
            all_topics = MCQ.objects.values_list("topic", flat=True).distinct()
            unexplored = [t for t in all_topics if t not in attempted_topics]
            
            for topic in unexplored[:max_suggestions - len(suggestions)]:
                suggestions.append(AISuggestion(
                    text=f"Explore new topic: '{topic}' at Easy level",
                    topic=topic,
                    recommended_difficulty="Easy",
                    rationale="Diversify your learning with a new subject",
                    stats={"unexplored": True},
                    priority=len(suggestions) + 1
                ))
        
        return suggestions[:max_suggestions]

    def recommend(self, user: Profile) -> AISuggestion:
        """Generate ML-based recommendation for the user"""
        if not self.is_trained:
            return AISuggestion(
                text="AI model is not trained yet. Please try again later.",
                topic=None,
                recommended_difficulty="Easy",
                rationale="Model training in progress.",
                stats={"model_trained": False},
            )
        
        # No history case
        any_quizzes = QuizResult.objects.filter(user=user)
        if not any_quizzes.exists():
            first_topic = MCQ.objects.values_list("topic", flat=True).distinct().order_by("topic").first()
            return AISuggestion(
                text=f"Start with an Easy quiz to build confidence" + (f" on '{first_topic}'" if first_topic else ""),
                topic=first_topic,
                recommended_difficulty="Easy",
                rationale="Start your learning journey with foundational questions",
                stats={"has_history": False, "model_prediction": "new_user"},
            )

        focus_topic = self._get_focus_topic(user)
        if not focus_topic:
            focus_topic = MCQ.objects.values_list("topic", flat=True).distinct().order_by("topic").first()

        if not focus_topic:
            return AISuggestion(
                text="No topics available for practice.",
                topic=None,
                recommended_difficulty="Easy",
                rationale="No topics found in database.",
                stats={"has_topics": False},
            )

        # Extract features for ML prediction
        try:
            features = self._extract_features(user, focus_topic)
            prediction = self.model.predict(features)[0]
            prediction_proba = self.model.predict_proba(features)[0]
            
            # Get confidence score (max probability as percentage)
            confidence = max(prediction_proba) * 100
            
            # Map prediction to action
            action_map = {0: "Easy", 1: "Medium", 2: "Hard", 3: "NextTopic"}
            predicted_action = action_map[prediction]
            
            # Generate suggestion based on ML prediction
            if predicted_action == "NextTopic":
                next_topic = self._find_next_topic(focus_topic)
                text = f"Great job mastering '{focus_topic}'! Try a new topic" + (f" like '{next_topic}'" if next_topic else "")
                return AISuggestion(
                    text=text,
                    topic=next_topic,
                    recommended_difficulty="Easy",
                    rationale="Based on your strong performance across all difficulty levels",
                    stats={
                        "model_prediction": predicted_action,
                        "confidence": confidence,
                        "current_topic": focus_topic,
                        "features": features.flatten().tolist()
                    },
                )
            else:
                text = f"Try {predicted_action} difficulty for '{focus_topic}'"
                return AISuggestion(
                    text=text,
                    topic=focus_topic,
                    recommended_difficulty=predicted_action,
                    rationale=f"Based on your performance history and learning progress",
                    stats={
                        "model_prediction": predicted_action,
                        "confidence": confidence,
                        "current_topic": focus_topic,
                        "features": features.flatten().tolist()
                    },
                )
                
        except Exception as e:
            # Fallback to simple rule-based suggestion
            return AISuggestion(
                text=f"Continue practicing on '{focus_topic}' - Easy level recommended",
                topic=focus_topic,
                recommended_difficulty="Easy",
                rationale="Continue building your skills with practice questions",
                stats={"ml_error": str(e), "fallback": True},
            )


# Keep the old rule-based engine as SuggestionEngine for backward compatibility
class SuggestionEngine(MLSuggestionEngine):
    """Alias for MLSuggestionEngine to maintain backward compatibility"""
    pass
