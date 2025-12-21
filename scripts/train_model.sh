#!/bin/bash
# train_model.sh

echo "🚀 Training ML Recommendation Model..."
echo "==============================================="

# Activate venv
source venv/Scripts/activate

# Run training script
python src/batch/ml_recommendation_spark.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Model training completed!"
    echo "📁 Model saved to: models/recommendation_model"
    echo ""
    echo "Next: Restart Flask to load the new model"
    echo "   python src/app.py"
else
    echo "❌ Training failed!"
    exit 1
fi