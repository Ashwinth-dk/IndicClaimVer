import sys
import io
import requests
import json

# Ensure UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE_URL = "http://127.0.0.1:8000"

print("=" * 60)
print("VERIFYING API ENDPOINTS & RETRIEVAL ENGINE")
print("=" * 60)

# 1. Health Check
try:
    health = requests.get(f"{BASE_URL}/api/health", timeout=5).json()
    print(f"1. Health Check: {health}")
except Exception as e:
    print(f"1. Health Check Failed: {e}")

# 2. Presets
try:
    presets = requests.get(f"{BASE_URL}/api/presets", timeout=5).json()
    print(f"2. Presets: Loaded {len(presets)} claims.")
except Exception as e:
    print(f"2. Presets Failed: {e}")

# 3. Bengali Claim Verification (Local Pool)
try:
    bengali_claim = "প্রতি ঘণ্টায় চাই হোম কোয়ারেন্টাইনদের ভিডিও! নয়া ঘোষণা কর্ণাটক সরকারের"
    res1 = requests.post(f"{BASE_URL}/api/verify", json={"claim": bengali_claim, "mode": "local"}, timeout=10).json()
    print(f"\n3. Bengali Claim: '{bengali_claim}'")
    print(f"   Verdict: [{res1.get('veracity')}] ({res1.get('display_veracity')}) | Confidence: {res1.get('confidence')*100:.1f}%")
    print(f"   Decisive Evidence: {res1.get('decisive_sentence', '')[:120]}...")
    print(f"   Explanation: {res1.get('explanation')}")
except Exception as e:
    print(f"3. Bengali Test Failed: {e}")

# 4. Hindi Claim Verification (Local Pool)
try:
    hindi_claim = "ममता बनर्जी ने किसी भी मंत्री को पद से नहीं हटाया"
    res2 = requests.post(f"{BASE_URL}/api/verify", json={"claim": hindi_claim, "mode": "local"}, timeout=10).json()
    print(f"\n4. Hindi Claim: '{hindi_claim}'")
    print(f"   Verdict: [{res2.get('veracity')}] ({res2.get('display_veracity')}) | Confidence: {res2.get('confidence')*100:.1f}%")
    print(f"   Decisive Evidence: {res2.get('decisive_sentence', '')[:120]}...")
except Exception as e:
    print(f"4. Hindi Test Failed: {e}")

# 5. English Claim Verification (Live Web Scraper Mode)
try:
    english_claim = "Ensure adequate buffer stock of medical oxygen: Centre to states"
    res3 = requests.post(f"{BASE_URL}/api/verify", json={"claim": english_claim, "mode": "live_web"}, timeout=10).json()
    print(f"\n5. English Claim (Live Web): '{english_claim}'")
    print(f"   Verdict: [{res3.get('veracity')}] ({res3.get('display_veracity')}) | Confidence: {res3.get('confidence')*100:.1f}%")
    print(f"   Retrieved Sources: {len(res3.get('retrieved_passages', []))}")
    if res3.get('retrieved_passages'):
        print(f"   Top Web Source: {res3['retrieved_passages'][0].get('source')}")
except Exception as e:
    print(f"5. English Test Failed: {e}")

# 6. Crawler Status & Trigger Check
try:
    trigger = requests.post(f"{BASE_URL}/api/crawl", json={"query": "COVID vaccine India fact check", "max_per_topic": 5}, timeout=5).json()
    print(f"\n6. Crawler Trigger: {trigger}")
    import time
    time.sleep(3)
    crawl_status = requests.get(f"{BASE_URL}/api/crawl/status", timeout=5).json()
    print(f"   Crawler Status: {crawl_status.get('status')} | Total Crawled: {crawl_status.get('total_crawled')}")
    if crawl_status.get('recent_samples'):
        sample = crawl_status['recent_samples'][-1]
        print(f"   Latest Crawled Sample: [{sample.get('Label')}] {sample.get('Text', '')[:60]}...")
except Exception as e:
    print(f"6. Crawler Status Failed: {e}")


# 7. Model Performance Metrics
try:
    metrics = requests.get(f"{BASE_URL}/api/metrics", timeout=5).json()
    print(f"\n7. Metrics Summary: Accuracy: {metrics.get('model_performance', {}).get('accuracy')*100:.2f}% | Train Samples: {metrics.get('dataset_statistics', {}).get('train_samples')}")
except Exception as e:
    print(f"7. Metrics Failed: {e}")

print("\n" + "=" * 60)
print("ALL VERIFICATION SUITE TESTS COMPLETED!")
print("=" * 60)
