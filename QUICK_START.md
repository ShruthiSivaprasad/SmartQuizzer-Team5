# Quick Start Guide - AI Suggestion System

## ✅ What's Been Implemented

### 1. Machine Learning Model
- **Decision Tree Classifier** trained on 200 synthetic samples
- **10 features** analyzing user performance across difficulty levels
- **4 prediction classes**: Easy, Medium, Hard, Next Topic
- Model automatically trains on first run and saves to `suggestion_model.pkl`

### 2. Multiple Suggestions
- Shows **up to 3 AI-powered recommendations** per user
- Ranked by priority: PRIMARY → ALTERNATIVE → OPTION
- Each suggestion includes:
  - Clear action text
  - Topic and difficulty
  - User-friendly rationale
  - Priority badge

### 3. Integration Points
- **User Dashboard**: Displays suggestions in prominent card
- **Analytics API**: Returns suggestions in JSON format
- **Auto-refresh**: Suggestions update based on latest quiz results

## 🚀 How to Use

### For Users
1. **Login** to your account
2. **Navigate** to User Dashboard
3. **View** AI-Powered Recommendations card
4. **Choose** from PRIMARY, ALTERNATIVE, or OPTION suggestions
5. **Take quizzes** to get better recommendations over time

### For Developers

#### Run the Server
```bash
cd /Users/shruthisivaprasad/Documents/Infy_Project/sample
python3 manage.py runserver
```

#### Test the AI Model
```bash
python3 manage.py test_ai_model
```

#### Access Suggestions via API
```bash
curl http://127.0.0.1:8000/analytics-data/
```

## 📊 How Suggestions Work

### New Users (No Quiz History)
```
PRIMARY: Start with Easy quiz on 'Python'
ALTERNATIVE: Explore 'C++' at Easy level  
OPTION: Explore 'Java' at Easy level
```

### Experienced Users (With Quiz History)
```
PRIMARY: Try Medium difficulty for 'Python'
  → When: 5+ Easy attempts with >80% average

ALTERNATIVE: Alternatively, try Hard on 'Python'
  → When: ML model sees potential for advancement

OPTION: Or explore 'C++' for variety
  → When: User shows mastery of current topic
```

## 🎯 ML Logic Summary

### Training Data (200 samples)
1. **Easy → Medium** (50 samples): ≥5 Easy attempts, >80% avg
2. **Medium → Hard** (50 samples): ≥5 Medium attempts, >75% avg
3. **Hard → Next Topic** (30 samples): ≥3 Hard attempts, >80% avg
4. **Beginners → Easy** (70 samples): Limited history

### Features Analyzed
- Attempt counts per difficulty (Easy, Medium, Hard)
- Average scores per difficulty
- Total quizzes and overall average
- Time patterns (days since first/last quiz)

### Prediction Process
1. Extract 10 features from user's QuizResult history
2. Run through trained Decision Tree model
3. Get probability distribution across 4 classes
4. Generate top 3 suggestions with probability > 15%
5. Format with user-friendly text and rationale

## 📁 Key Files

```
sample/
├── base/
│   ├── ai.py                    # ML engine and suggestion logic
│   ├── views.py                 # Dashboard and API views
│   ├── models.py                # QuizResult, Profile models
│   ├── templates/
│   │   └── user_dashboard.html  # Displays suggestions
│   └── management/
│       └── commands/
│           └── test_ai_model.py # Test command
├── requirements.txt             # Dependencies (scikit-learn, numpy)
├── suggestion_model.pkl         # Trained model (auto-generated)
├── AI_SUGGESTION_SYSTEM.md      # Full documentation
└── QUICK_START.md               # This file
```

## 🔧 Configuration

### Change Number of Suggestions
Edit `base/views.py`:
```python
suggestions = engine.get_multiple_suggestions(user, max_suggestions=3)  # Change 3 to desired number
```

### Adjust Suggestion Threshold
Edit `base/ai.py`:
```python
if prob > 0.15:  # Change 0.15 to adjust sensitivity
```

## 🐛 Troubleshooting

### Issue: No suggestions showing
**Solution**: Check if `ai_suggestions` exists in template context
```python
# In base/views.py
print(context['ai_suggestions'])  # Debug output
```

### Issue: Model not trained
**Solution**: Delete model file and restart
```bash
rm suggestion_model.pkl
python3 manage.py runserver
```

### Issue: Wrong suggestions
**Solution**: Model needs more real data
- Take more quizzes to generate training data
- Consider retraining with actual user patterns

## 📈 What Users See

### Dashboard Card
```
┌────────────────────────────────────────────┐
│ 💡 AI-Powered Recommendations              │
├────────────────────────────────────────────┤
│ [PRIMARY] Try Medium difficulty for 'Python'│
│ Based on your performance history...       │
│                                   [Medium] │
├────────────────────────────────────────────┤
│ [ALTERNATIVE] Alternatively, try Hard...   │
│ Another good option based on your progress │
│                                     [Hard] │
└────────────────────────────────────────────┘
```

### Features
- ✅ Color-coded priority badges
- ✅ Clear action text
- ✅ Difficulty badges
- ✅ User-friendly rationale
- ✅ No technical ML jargon
- ✅ Responsive design

## 🎓 Educational Benefits

1. **Personalized Learning Path**: Adapts to individual progress
2. **Progressive Difficulty**: Guides users through levels
3. **Topic Variety**: Suggests exploring new subjects
4. **Confidence Building**: Starts with appropriate difficulty
5. **Engagement**: Multiple options keep learning interesting

## 📝 Next Steps

### Immediate
1. ✅ System is ready to use
2. ✅ Take quizzes to see suggestions evolve
3. ✅ Monitor user engagement with suggestions

### Future Improvements
- Collect feedback on suggestion quality
- Retrain model with real user data
- Add A/B testing for different algorithms
- Implement "Why this suggestion?" tooltips
- Auto-fill quiz form with primary suggestion

## 💡 Tips

- **For Best Results**: Take at least 5 quizzes per difficulty level
- **Variety**: Try different topics to get diverse suggestions
- **Consistency**: Regular practice improves suggestion accuracy
- **Feedback**: User actions help improve future recommendations

## 🔗 Related Documentation

- Full system documentation: `AI_SUGGESTION_SYSTEM.md`
- Django models: `base/models.py`
- ML implementation: `base/ai.py`
- API endpoints: `base/views.py`

---

**Status**: ✅ Fully Implemented and Ready to Use
**Last Updated**: October 2, 2025
