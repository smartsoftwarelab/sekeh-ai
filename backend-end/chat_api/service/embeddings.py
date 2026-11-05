import numpy as np
import requests
from config import Config


def get_embedding(text: str, task_type: str | None = None):
    """
    Embedding (bge-m3)
    task_type فقط برای سازگاری امضا نگه داشته شده.
    """
    text = (text or "").strip()
    if not text:
        return np.zeros((Config.EMBED_EXPECTED_DIM,), dtype=float)

    payload = {
        "model": Config.EMBED_MODEL,
        "input": [text[:4000]],
        "encoding_format": "float"
    }

    try:
        r = requests.post(
            f"{(Config.EMBED_BASE_URL or '').rstrip('/')}/v1/embeddings",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=Config.EMBED_TIMEOUT,
        )
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"Embedding API error: {e}")
        return np.zeros((Config.EMBED_EXPECTED_DIM,), dtype=float)

    try:
        data = r.json()
        vec = data["data"][0]["embedding"]
        arr = np.array(vec, dtype=float)
    except (KeyError, IndexError, ValueError) as e:
        print(f"Embedding response parse error: {e}")
        return np.zeros((Config.EMBED_EXPECTED_DIM,), dtype=float)

    # نرمال‌سازی ابعاد
    if arr.size != Config.EMBED_EXPECTED_DIM:
        if arr.size < Config.EMBED_EXPECTED_DIM:
            padded = np.zeros((Config.EMBED_EXPECTED_DIM,), dtype=float)
            padded[:arr.size] = arr
            arr = padded
        else:
            arr = arr[:Config.EMBED_EXPECTED_DIM]

    return arr


def cosine_similarity(a, b) -> float:
    """
    محاسبه شباهت کسینوسی بین دو vector
    نتیجه: مقدار بین 0 و 1
    """
    try:
        # تبدیل به numpy array و flatten کنید
        a = np.array(a, dtype=float).flatten()
        b = np.array(b, dtype=float).flatten()
        
        # بررسی سایز برابر
        if a.size == 0 or b.size == 0:
            return 0.0
        
        if a.size != b.size:
            # اگر سایز متفاوت باشد، کوچک‌تر را pad کنید
            min_size = min(a.size, b.size)
            a = a[:min_size]
            b = b[:min_size]
        
        # محاسبه norm
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        
        # محاسبه cosine similarity
        similarity = float(np.dot(a, b) / (norm_a * norm_b))
        
        # کلمپ کنید به [0, 1]
        return max(0.0, min(1.0, similarity))
    
    except Exception as e:
        print(f"Cosine similarity error: {e}")
        return 0.0


def clamp_percent(score: float) -> int:
    """
    تبدیل score (0-1) به درصد (0-100)
    """
    try:
        # اطمینان از float
        score = float(score)
        
        # کلمپ کنید به [0, 1]
        clamped = max(0.0, min(1.0, score))
        
        # تبدیل به درصد و round کنید
        percent = int(round(clamped * 100))
        
        return percent
    except (TypeError, ValueError):
        return 0