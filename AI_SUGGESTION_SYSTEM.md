# AI Quiz Suggestion System Documentation

## Overview
This document describes the AI-powered suggestion system that recommends personalized next steps for users based on their MCQ quiz performance history.

## System Architecture

### 1. Machine Learning Model
- **Algorithm**: Decision Tree Classifier (scikit-learn)
- **Model Type**: Supervised learning with synthetic training data
- **Model File**: `base/ai.py`
- **Persistence**: Trained model saved as `suggestion_model.pkl`

### 2. Features Used (10 dimensions)

The ML model analyzes the following features for each user:

| Feature | Description |
|---------|-------------|
| Easy Attempts | Number of Easy level quizzes attempted |
| Easy Average | Average score on Easy level quizzes |
| Medium Attempts | Number of Medium level quizzes attempted |
| Medium Average | Average score on Medium level quizzes |
| Hard Attempts | Number of Hard level quizzes attempted |
| Hard Average | Average score on Hard level quizzes |
| Total Quizzes | Total number of quizzes taken |
| Overall Average | Average score across all difficulty levels |
| Days Since First | Days elapsed since first quiz |
| Days Since Last | Days elapsed since last quiz |

### 3. Training Data

The model is trained on **200 synthetic samples** based on educational best practices:

#### Rule 1: Easy Mastery → Medium (50 samples)
- **Condition**: ≥5 Easy attempts AND >80% average
- **Recommendation**: Advance to Medium difficulty

#### Rule 2: Medium Mastery → Hard (50 samples)
- **Condition**: ≥5 Medium attempts AND >75% average
- **Recommendation**: Level up to Hard difficulty

#### Rule 3: Hard Mastery → Next Topic (30 samples)
- **Condition**: ≥3 Hard attempts AND >80% average
- **Recommendation**: Move to a new topic

#### Rule 4: Beginners → Easy (70 samples)
- **Condition**: Limited quiz history or mixed performance
- **Recommendation**: Continue with Easy level

### 4. Prediction Classes

The model predicts one of 4 actions:
- **0**: Suggest Easy difficulty
- **1**: Suggest Medium difficulty
- **2**: Suggest Hard difficulty
- **3**: Suggest moving to next topic

## Multiple Suggestions Feature

### How It Works
The system now provides **up to 3 suggestions** ranked by priority:

1. **PRIMARY**: The top ML prediction (highest confidence)
2. **ALTERNATIVE**: Second-best option based on probability
3. **OPTION**: Third alternative if probability > 15%

### Suggestion Generation Logic

```python
def get_multiple_suggestions(user, max_suggestions=3):
    1. Get primary ML prediction
    2. Get prediction probabilities for all 4 classes
    3. Sort by probability (descending)
    4. For top 3 predictions with probability > 15%:
       - Generate user-friendly suggestion text
       - Assign priority (1=primary, 2=alternative, 3=option)
    5. Return list of suggestions
```

### For New Users
- Suggests multiple topics at Easy level
- Helps users explore different subjects

### For Experienced Users
- Primary: Best next step based on performance
- Alternative: Different difficulty on same topic
- Option: Explore new topic for variety

## Implementation Details

### Files Modified

#### 1. `base/ai.py`
- `AISuggestion` dataclass with priority field
- `MLSuggestionEngine` class with Decision Tree
- `get_multiple_suggestions()` method
- `recommend()` method (single suggestion)
- Training data generation
- Model persistence (save/load)

#### 2. `base/views.py`
- `dashboard_view()`: Uses `get_multiple_suggestions()`
- `analytics_data_view()`: Returns multiple suggestions in API
- Context updated: `ai_suggestions` (list) instead of `ai_suggestion` (single)

#### 3. `base/templates/user_dashboard.html`
- Displays multiple suggestions in card format
- Priority badges (PRIMARY/ALTERNATIVE/OPTION)
- Color-coded by priority
- Responsive layout with difficulty badges

#### 4. `requirements.txt`
```
Django>=4.0.0
PyMuPDF>=1.20.0
scikit-learn>=1.0.0
numpy>=1.21.0
```

### Database Models Used

#### QuizResult
```python
- user (ForeignKey to Profile)
- topic (CharField)
- difficulty_level (CharField)
- total_questions (IntegerField)
- correct_answers (IntegerField)
- score_percentage (FloatField)
- date_taken (DateTimeField)
```

#### MCQ
```python
- topic (CharField)
- difficulty_level (CharField)
- question (TextField)
- options (a, b, c, d)
- correct_answer (CharField)
```

## User Experience

### Dashboard Display

```
┌─────────────────────────────────────────────────────┐
│ 💡 AI-Powered Recommendations                       │
├─────────────────────────────────────────────────────┤
│ [PRIMARY] Try Medium difficulty for 'Python'        │
│ Based on your performance history and learning...   │
│                                          [Medium]    │
├─────────────────────────────────────────────────────┤
│ [ALTERNATIVE] Alternatively, try Hard on 'Python'   │
│ Another good option based on your progress          │
│                                            [Hard]    │
├─────────────────────────────────────────────────────┤
│ [OPTION] Or explore 'C++' for variety               │
│ Diversify your learning with a new topic            │
│                                            [Easy]    │
└─────────────────────────────────────────────────────┘
```

### Rationale Messages (User-Friendly)
- ✅ "Based on your performance history and learning progress"
- ✅ "Start your learning journey with foundational questions"
- ✅ "Another good option based on your progress"


## API Endpoints

### GET `/analytics-data/`
Returns analytics including AI suggestions:

```json
{
  "topic_performance": {...},
  "quiz_history_analytics": [...],
  "ai_suggestions": [
    {
      "text": "Try Medium difficulty for 'Python'",
      "topic": "Python",
      "recommended_difficulty": "Medium",
      "rationale": "Based on your performance history...",
      "priority": 1,
      "stats": {
        "model_prediction": "Medium",
        "confidence": 87.3,
        "current_topic": "Python"
      }
    },
    {...},
    {...}
  ]
}
```

## Testing

### Management Command
```bash
python3 manage.py test_ai_model
```

**Output:**
```
Testing AI Suggestion Model...
✓ Model is trained and ready

--- Testing with user: shruthisivaprasad ---
Suggestion: Try Medium difficulty for 'Python'
Topic: Python
Difficulty: Medium
Rationale: Based on your performance history and learning progress
ML Confidence: 100.0%
Model Prediction: Medium
```

## Model Performance

### Advantages
1. **Adaptive**: Learns from user behavior patterns
2. **Temporal Awareness**: Considers quiz timing
3. **Progressive**: Guides through difficulty levels
4. **Extensible**: Easy to retrain or swap models

## Configuration

### Adjust Number of Suggestions
In `base/views.py`:
```python
suggestions = engine.get_multiple_suggestions(user, max_suggestions=3)
```

### Adjust Probability Threshold
In `base/ai.py`:
```python
if prob > 0.15:  # Only suggest if probability > 15%
```

### Model Hyperparameters
In `base/ai.py`:
```python
self.model = DecisionTreeClassifier(
    max_depth=10,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42
)
```

## Troubleshooting

### Model Not Training
- Check if numpy and scikit-learn are installed
- Delete `suggestion_model.pkl` and restart server
- Check console for training errors

### No Suggestions Displayed
- Verify `ai_suggestions` is in template context
- Check if user has quiz history
- Inspect browser console for JavaScript errors

### Wrong Suggestions
- Model may need retraining with real data
- Check if QuizResult data is accurate
- Verify feature extraction logic

## Credits
- **ML Framework**: scikit-learn
- **Algorithm**: Decision Tree Classifier
- **Training Approach**: Synthetic data based on educational best practices
- **Integration**: Django views and templates
