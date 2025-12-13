import pickle
from flask import Flask, render_template, request
from feature_extraction import extract_features
import numpy as np
import os

app = Flask(__name__)

# Load model
MODEL_PATH = os.path.join("model", "phishing_model.pkl")
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    try:
        url = request.form.get("url", "").strip()
        if not url:
            return render_template("index.html", error="Please enter a URL.")

        # ensure scheme for feature extraction (optional)
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "http://" + url

        features = extract_features(url)         # returns list
        features_arr = np.array(features).reshape(1, -1)

        pred = model.predict(features_arr)[0]    # 0 or 1
        prob = model.predict_proba(features_arr)[0] if hasattr(model, "predict_proba") else None

        label_text = "Phishing Website — DO NOT TRUST" if pred == 1 else "Legitimate / Safe Website"
        confidence = None
        if prob is not None:
            # choose probability for predicted class
            confidence = round(float(prob[pred]) * 100, 2)

        return render_template("result.html",
                               url=url,
                               prediction=label_text,
                               confidence=confidence)
    except Exception as e:
        return render_template("index.html", error=f"Error: {e}")

#--if __name__ == "__main__":
    #app.run(debug=True)
if __name__ == "__main__":
    app.run()
