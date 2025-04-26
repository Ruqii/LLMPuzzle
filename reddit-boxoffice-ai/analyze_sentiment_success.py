# analyze_sentiment_success.py

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import os

# Step 0: Ensure folders exist
os.makedirs("plots", exist_ok=True)

# Step 1: Load sentiment data and create label file
sentiment_df = pd.read_csv("data/reddit_sentiment.csv")

# Define manual box office success labels
label_data = pd.DataFrame({
    "movie": ["dune2", "venom2", "gladiator", "thewildrobot", "backtoblack"],
    "box_office": [700, 506, 465, 90, 35],
    "success_tag": ["successful", "successful", "average", "unsuccessful", "unsuccessful"]
})

label_data.to_csv("data/labels.csv", index=False)

# Merge labels with sentiment
sentiment_df = sentiment_df.merge(label_data, on="movie", how="left")
sentiment_df.to_csv("data/reddit_sentiment_labeled.csv", index=False)

# Step 2: Load merged sentiment + success data
df = sentiment_df.copy()

# Step 3: Encode sentiment and extract basic text features
label_map = {"positive": 1, "neutral": 0, "negative": -1}
df["sentiment_score"] = df["sentiment"].str.lower().map(label_map)
df["comment_length"] = df["combined_text"].fillna("").apply(len)

print("🧪 Unique sentiment values:", df["sentiment"].dropna().unique())
# Drop rows with missing labels or features
df = df.dropna(subset=["sentiment_score", "success_tag"])

print(f"📊 Rows after filtering: {len(df)}")
print(df[['movie', 'sentiment', 'sentiment_score', 'success_tag']].head())

# Step 4: Model preparation
X = df[["sentiment_score", "comment_length"]]
y = df["success_tag"]

le = LabelEncoder()
y_encoded = le.fit_transform(y)

X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.3, random_state=42, stratify=y_encoded)

# Step 5: Train model
model = RandomForestClassifier(random_state=42)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

# Step 6: Results
print("\n🎯 Classification Report:")
print(classification_report(y_test, y_pred, target_names=le.classes_))

cm = confusion_matrix(y_test, y_pred, labels=range(len(le.classes_)))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=le.classes_, yticklabels=le.classes_)
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Confusion Matrix")
plt.savefig("plots/confusion_matrix.png")
plt.show()