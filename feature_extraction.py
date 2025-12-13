import re
from urllib.parse import urlparse

# Trusted parent / partner domains
TRUSTED_DOMAINS = [
    "google.com",
    "facebook.com",
    "github.com",
    "amazon.com",
    "microsoft.com",
    "apple.com",
    "paypal.com",
    "linkedin.com",
    "netflix.com",
    "twitter.com",
    "instagram.com",

    # Education / Training / Enterprise
    "infosys.com",
    "onwingspan.com",
    "springboard.com",
    "coursera.org",
    "edx.org",
    "nptel.ac.in",
    "swayam.gov.in",

    # Cloud / Dev
    "cloudflare.com",
    "aws.amazon.com",
    "azure.microsoft.com",
    "googleapis.com"
]

def extract_features(url):
    features = []

    # 1️⃣ URL length
    features.append(len(url))

    # 2️⃣ Count of dots
    features.append(url.count('.'))

    # 3️⃣ Check for @ symbol
    features.append(1 if '@' in url else 0)

    # 4️⃣ Check for IP address in URL
    ip_pattern = r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+'
    features.append(1 if re.search(ip_pattern, url) else 0)

    # 5️⃣ HTTPS or not
    features.append(1 if url.startswith("https") else 0)

    # 6️⃣ Trusted domain feature (NEW)
    domain = urlparse(url).netloc.lower()
    features.append(
        1 if any(trusted in domain for trusted in TRUSTED_DOMAINS) else 0
    )

    return features
