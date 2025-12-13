import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import pickle
from feature_extraction import extract_features

# Load dataset
df = pd.read_csv("dataset/urls.csv")

# Extract features
X = df["url"].apply(extract_features).tolist()
y = df["label"].map({"legitimate": 0, "phishing": 1})

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Model
model = RandomForestClassifier()
model.fit(X_train, y_train)

# Save model
pickle.dump(model, open("model/phishing_model.pkl", "wb"))

print("Model training completed!")
