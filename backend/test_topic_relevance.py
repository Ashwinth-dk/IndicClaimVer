import unittest
import asyncio
from app.crawlers.topic_filter import TopicRelevanceFilter

class TestTopicRelevanceFilter(unittest.TestCase):

    def test_on_topic_exact_match(self):
        query = "COVID-19 vaccination drive"
        title = "India completes massive COVID-19 vaccination drive across all states"
        is_rel, score, reason = TopicRelevanceFilter.is_relevant(query, title)
        self.assertTrue(is_rel, f"Should be relevant: {reason}")
        self.assertGreaterEqual(score, 0.5)

    def test_on_topic_indic_tamil(self):
        query = "தமிழ்நாடு தேர்தல் முடிவு 2026"
        title = "தமிழ்நாடு சட்டமன்ற தேர்தல் முடிவு மற்றும் வாக்கு எண்ணிக்கை நேரலை"
        is_rel, score, reason = TopicRelevanceFilter.is_relevant(query, title)
        self.assertTrue(is_rel, f"Tamil query should match: {reason}")

    def test_on_topic_indic_hindi(self):
        query = "चंद्रयान 3 मिशन"
        title = "इसरो का चंद्रयान 3 मिशन चंद्रमा के दक्षिणी ध्रुव पर सफलतापूर्वक उतरा"
        is_rel, score, reason = TopicRelevanceFilter.is_relevant(query, title)
        self.assertTrue(is_rel, f"Hindi query should match: {reason}")

    def test_off_topic_food_rejected(self):
        query = "ISRO space launch Aditya L1"
        title = "Delicious authentic Vietnamese pho recipe for dinner"
        snippet = "Learn how to make rich beef broth with star anise and fresh rice noodles."
        is_rel, score, reason = TopicRelevanceFilter.is_relevant(query, title, snippet=snippet)
        self.assertFalse(is_rel, f"Irrelevant food article must be rejected: {reason}")

    def test_off_topic_social_media_tool_rejected(self):
        query = "Election Commission voting guidelines"
        title = "Instagram Story Viewer Online Free Anonymous"
        snippet = "View Instagram stories anonymously without an account or login."
        is_rel, score, reason = TopicRelevanceFilter.is_relevant(query, title, snippet=snippet)
        self.assertFalse(is_rel, f"Social media tool spam must be rejected: {reason}")

    def test_off_topic_random_news_rejected(self):
        query = "Kongu Engineering College"
        title = "Premier League football highlights: Arsenal defeats Chelsea 2-1"
        snippet = "Arsenal scored in the final minutes to secure a thrilling victory in London derby."
        is_rel, score, reason = TopicRelevanceFilter.is_relevant(query, title, snippet=snippet)
        self.assertFalse(is_rel, f"Unrelated sports news must be rejected: {reason}")

    def test_strict_feed_mode_rejects_single_token_coincidence(self):
        query = "Kongu Engineering College campus placement"
        # A generic news article that only contains the word "college" or "engineering" by coincidence
        title = "Engineering student builds solar-powered car in Delhi"
        snippet = "A college student from Delhi designed an eco-friendly vehicle."
        is_rel, score, reason = TopicRelevanceFilter.is_relevant(
            query, title, snippet=snippet, strict_feed_mode=True
        )
        self.assertFalse(is_rel, f"Strict feed mode should reject weak partial matches: {reason}")

    def test_strict_feed_mode_accepts_strong_match(self):
        query = "Kongu Engineering College campus placement"
        title = "Kongu Engineering College announces record 95% campus placement for 2026 batch"
        snippet = "Top multinational companies visit Kongu Engineering College for recruitment drive."
        is_rel, score, reason = TopicRelevanceFilter.is_relevant(
            query, title, snippet=snippet, strict_feed_mode=True
        )
        self.assertTrue(is_rel, f"Strict feed mode should accept strong matches: {reason}")

if __name__ == "__main__":
    unittest.main()
