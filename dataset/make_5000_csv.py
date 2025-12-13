import pandas as pd
import random

legit_sites = [
    "google.com", "facebook.com", "github.com", "amazon.com", "microsoft.com",
    "apple.com", "linkedin.com", "netflix.com", "paypal.com", "twitter.com",
    "instagram.com", "wikipedia.org", "openai.com", "stackoverflow.com"
]

phishing_terms = [
    "login", "verify", "secure", "update", "account",
    "bank", "confirm", "alert", "support", "billing"
]

rows = []

# 2500 legitimate URLs
for _ in range(2500):
    site = random.choice(legit_sites)
    rows.append([f"https://{site}/", "legitimate"])

# 2500 phishing URLs
for _ in range(2500):
    term = random.choice(phishing_terms)
    num = random.randint(1000, 99999)
    rows.append([f"http://{term}-security{num}.freehost.net/login", "phishing"])

random.shuffle(rows)

df = pd.DataFrame(rows, columns=["url", "label"])
df.to_csv("dataset/urls_5000.csv", index=False)

print("✅ urls_5000.csv created successfully!")
