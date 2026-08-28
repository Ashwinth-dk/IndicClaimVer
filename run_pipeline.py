import argparse
import sys
import json
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


from backend.config import API_HOST, API_PORT
from backend.data_pipeline import load_and_preprocess_dataset, get_dataset_statistics
from backend.retriever import get_retriever
from backend.sentence_selector import get_sentence_selector
from backend.veracity_model import get_veracity_model
from backend.scraper.crawler import get_crawler
from backend.scraper.live_search import search_live_web_evidence

def run_data_tests():
    print("=" * 60)
    print("1. RUNNING DATA PIPELINE VERIFICATION")
    print("=" * 60)
    stats = get_dataset_statistics()
    print("Dataset Statistics:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    train_df, dev_df = load_and_preprocess_dataset()
    print(f"\nTrain set preview (total {len(train_df)} rows):")
    print(train_df[["claim", "label_str"]].head(3))
    print(f"\nDev set preview (total {len(dev_df)} rows):")
    print(dev_df[["claim", "label_str"]].head(3))
    print("\n✓ Data pipeline verification successful!\n")

def run_retriever_tests():
    print("=" * 60)
    print("2. RUNNING EVIDENCE RETRIEVER TESTS")
    print("=" * 60)
    retriever = get_retriever()
    test_claims = [
        "প্রতি ঘণ্টায় চাই হোম কোয়ারেন্টাইনদের ভিডিও! নয়া ঘোষণা কর্ণাটক সরকারের",
        "ममता बनर्जी ने किसी भी मंत्री को पद से नहीं हटाया",
        "Ensure adequate buffer stock of medical oxygen: Centre to states"
    ]
    for claim in test_claims:
        print(f"\nQuery Claim: {claim}")
        results = retriever.retrieve(claim, top_k=2)
        for r in results:
            print(f"  [Match Score: {r['score']*100:.1f}%] ID: {r['id']}")
            print(f"  Snippet: {r['evidence'][:150]}...")
    print("\n✓ Evidence retriever test completed successfully!\n")

def run_scraper_tests():
    print("=" * 60)
    print("3. RUNNING WEB SCRAPER & CRAWLER TESTS")
    print("=" * 60)
    crawler = get_crawler()
    query = "COVID vaccine India fact check"
    print(f"Executing test crawl for query: '{query}'...")
    results = crawler.crawl_google_factcheck(query, max_results=5)
    print(f"Harvested {len(results)} fact-checked articles:")
    for item in results[:3]:
        print(f"  - Claim: {item['Text'][:80]}...")
        print(f"    Label: {item['Label']} | Publisher: {item['Publisher']}")
        print(f"    Evidence: {item['Evidence'][:100]}...")
    print("\n✓ Web scraper test completed successfully!\n")

def run_evaluation():
    print("=" * 60)
    print("4. RUNNING END-TO-END VERACITY EVALUATION")
    print("=" * 60)
    retriever = get_retriever()
    selector = get_sentence_selector()
    model = get_veracity_model()
    
    _, dev_df = load_and_preprocess_dataset()
    sample_df = dev_df.head(20)
    
    correct = 0
    total = len(sample_df)
    
    print(f"Evaluating {total} multi-lingual test samples end-to-end:")
    for idx, row in sample_df.iterrows():
        claim = row["claim"]
        gold_label = row["label_str"]
        gold_ev = row["evidence"]
        
        # Test veracity prediction
        pred = model.predict(claim, gold_ev)
        is_match = (pred["veracity"] == gold_label)
        if is_match:
            correct += 1
            
        print(f"Sample #{idx+1}: [{pred['veracity']}] (Gold: [{gold_label}]) - {'✓ MATCH' if is_match else '✗ MISMATCH'}")
        print(f"  Claim: {claim[:70]}...")
        print(f"  Confidence: {pred['confidence']*100:.1f}%")
        
    accuracy = correct / total
    print(f"\nSample Subset Accuracy: {accuracy*100:.2f}% ({correct}/{total})")
    print("✓ End-to-end evaluation completed successfully!\n")

def run_training(epochs=3, batch_size=8, lr=2e-5):
    print("=" * 60)
    print("STARTING MODEL TRAINING & FINE-TUNING PIPELINE")
    print(f"Epochs: {epochs} | Batch Size: {batch_size} | Learning Rate: {lr}")
    print("=" * 60)
    from backend.trainer import get_trainer
    trainer = get_trainer()
    metrics = trainer.train(include_crawled=True, epochs=epochs, batch_size=batch_size, lr=lr)
    print("\nTraining Completed!")
    print(f"Final Validation Accuracy: {metrics.get('accuracy', 0)*100:.2f}%")
    print(f"Final Validation F1: {metrics.get('f1_macro', 0)*100:.2f}%")
    print(f"Model saved to: {trainer.output_dir}")

def run_scrape(count: int = 25):
    print("=" * 60)
    print(f"HARVESTING {count} FACT-CHECKED SAMPLES (4-FIELD SCHEMA)")
    print("=" * 60)
    from backend.scraper.dataset_scraper import DatasetScraper
    scraper = DatasetScraper()
    items = scraper.scrape_multi_domain_dataset(target_count=count)
    scraper.save_dataset(items, append=False)
    print(f"\n✓ Scraped {len(items)} samples matching train_subtask1.json structure!\n")

def run_test_scraped():
    print("=" * 60)
    print("TESTING TRAINED MODEL ON SCRAPED 4-FIELD DATASET")
    print("=" * 60)
    from test_scraped_data import evaluate_model
    evaluate_model()

def start_server():
    import uvicorn
    print("=" * 60)
    print(f"LAUNCHING VERICLAIM AI SERVER ON http://{API_HOST}:{API_PORT}")
    print("=" * 60)
    uvicorn.run("backend.app:app", host=API_HOST, port=API_PORT, reload=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VeriClaim AI Master CLI")
    parser.add_argument("--test-data", action="store_true", help="Test dataset loading and preprocessing")
    parser.add_argument("--test-retriever", action="store_true", help="Test contextual evidence retriever")
    parser.add_argument("--test-scraper", action="store_true", help="Test web scraper and live search")
    parser.add_argument("--scrape", action="store_true", help="Scrape new fact-checked data with 4-field structure")
    parser.add_argument("--test-scraped", action="store_true", help="Test trained model on scraped dataset")
    parser.add_argument("--count", type=int, default=25, help="Number of samples to scrape (default: 25)")
    parser.add_argument("--evaluate", action="store_true", help="Run end-to-end evaluation")
    parser.add_argument("--train", action="store_true", help="Train the veracity prediction model on dataset")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs (default: 3)")
    parser.add_argument("--batch-size", type=int, default=8, help="Training batch size (default: 8)")
    parser.add_argument("--server", action="store_true", help="Start FastAPI Web Application server")

    args = parser.parse_args()

    if args.scrape:
        run_scrape(count=args.count)
    elif args.test_scraped:
        run_test_scraped()
    elif args.test_data:
        run_data_tests()
    elif args.test_retriever:
        run_retriever_tests()
    elif args.test_scraper:
        run_scraper_tests()
    elif args.evaluate:
        run_evaluation()
    elif args.train:
        run_training(epochs=args.epochs, batch_size=args.batch_size)
    elif args.server:
        start_server()
    else:
        # Default: run full test suite then launch server
        run_data_tests()
        run_retriever_tests()
        run_scraper_tests()
        run_evaluation()
        start_server()


