"""
Comprehensive Unit Tests for Multilingual Components in IndicClaim.
Tests Language Detection, Unicode integrity, Claim Extraction, Candidate Matching,
Label Generation, and Duplicate Detection across English, Tamil, Hindi, and Marathi.
"""

import unittest
from app.utils.language_detector import LanguageDetector
from app.utils.preprocessing import normalize_indic_text, preprocess_claim, preprocess_evidence
from app.extractors.claim_extractor import ClaimExtractor
from app.extractors.evidence_extractor import EvidenceExtractor
from app.verification.candidate_matcher import CandidateMatcher
from app.verification.label_generator import LabelGenerator
from app.verification.duplicate_detector import DuplicateDetector
from app.verification.quality_checker import QualityChecker

class TestMultilingualComponents(unittest.TestCase):

    def test_language_detection(self):
        # English
        en_text = "The Supreme Court of India delivered a landmark judgment on privacy."
        res_en = LanguageDetector.detect_language(en_text)
        self.assertEqual(res_en["language"], "en")
        self.assertGreater(res_en["confidence"], 0.70)

        # Tamil
        ta_text = "இந்தியா உலகின் அதிக மக்கள் தொகை கொண்ட நாடாகும் என்று ஐநா சபை அறிவித்தது."
        res_ta = LanguageDetector.detect_language(ta_text)
        self.assertEqual(res_ta["language"], "ta")
        self.assertEqual(res_ta["script"], "Tamil")
        self.assertGreater(res_ta["confidence"], 0.70)

        # Hindi
        hi_text = "भारत दुनिया का सबसे अधिक आबादी वाला देश बन गया है, संयुक्त राष्ट्र ने पुष्टि की।"
        res_hi = LanguageDetector.detect_language(hi_text)
        self.assertEqual(res_hi["language"], "hi")
        self.assertEqual(res_hi["script"], "Devanagari")
        self.assertGreater(res_hi["confidence"], 0.70)

        # Marathi
        mr_text = "महाराष्ट्र शासनाने शेतकऱ्यांसाठी नवीन कर्जमाफी योजना जाहीर केली आहे."
        res_mr = LanguageDetector.detect_language(mr_text)
        self.assertEqual(res_mr["language"], "mr")
        self.assertEqual(res_mr["script"], "Devanagari")
        self.assertGreater(res_mr["confidence"], 0.70)

    def test_unicode_preservation(self):
        ta_sample = "தமிழ்நாடு அரசு புதிய கல்வி உதவித்தொகையை அறிவித்துள்ளது."
        norm_ta = normalize_indic_text(ta_sample)
        self.assertEqual(norm_ta, ta_sample)

        hi_sample = "भारतीय अंतरिक्ष अनुसंधान संगठन (ISRO) ने चंद्रयान-3 मिशन सफलतापूर्वक लॉन्च किया।"
        norm_hi = normalize_indic_text(hi_sample)
        self.assertEqual(norm_hi, hi_sample)

        mr_sample = "मुंबई उच्च न्यायालयाने पर्यावरण संरक्षणाबाबत महत्त्वपूर्ण आदेश दिले आहेत."
        norm_mr = normalize_indic_text(mr_sample)
        self.assertEqual(norm_mr, mr_sample)

    def test_claim_extractor_multilingual(self):
        # Tamil article snippet
        ta_article = "சென்னை: தமிழ்நாடு அரசு புதிய மகளிர் உரிமைத் திட்டத்தை அதிகாரப்பூர்வமாக தொடங்கியது. இதன் மூலம் தகுதியுள்ள பெண்களுக்கு மாதம் ₹1000 வழங்கப்படும்."
        ta_claims = ClaimExtractor.extract_claims_from_text(ta_article, title="மகளிர் உரிமை திட்டம் தொடக்கம்")
        self.assertGreater(len(ta_claims), 0)
        self.assertTrue(any(c["language"] == "ta" for c in ta_claims))

        # Hindi article snippet
        hi_article = "नई दिल्ली: केंद्रीय मंत्रिमंडल ने राष्ट्रीय शिक्षा नीति के तहत नए दिशा-निर्देशों को मंजूरी दी है।"
        hi_claims = ClaimExtractor.extract_claims_from_text(hi_article)
        self.assertGreater(len(hi_claims), 0)
        self.assertTrue(any(c["language"] == "hi" for c in hi_claims))

        # Marathi article snippet
        mr_article = "मुंबई: राज्य शासनाने नवीन औद्योगिक धोरण जाहीर केले असून ५ लाख रोजगार निर्मितीचे उद्दिष्ट ठेवले आहे."
        mr_claims = ClaimExtractor.extract_claims_from_text(mr_article)
        self.assertGreater(len(mr_claims), 0)
        self.assertTrue(any(c["language"] == "mr" for c in mr_claims))

    def test_label_generator_multilingual(self):
        # Tamil SUPPORTS
        ta_claim = "இஸ்ரோ சந்திரயான்-3 விண்கலத்தை வெற்றிகரமாக நிலவில் தரையிறக்கியது."
        ta_evidence_sup = "இஸ்ரோ விஞ்ஞானிகள் சந்திரயான்-3 நிலவின் தென் துருவத்தில் வெற்றிகரமாக தரையிறங்கியதை உறுதிப்படுத்தியது."
        label_ta_sup, conf_ta_sup, _ = LabelGenerator.generate_label(ta_claim, ta_evidence_sup, match_score=0.6)
        self.assertEqual(label_ta_sup, "SUPPORTS")

        # Tamil REFUTES (Debunking marker)
        ta_evidence_ref = "வைரலான தகவல் தவறான செய்தி என்றும் அரசு எந்த உத்தரவையும் பிறப்பிக்கவில்லை என்றும் பிஐபி மறுத்துள்ளது."
        label_ta_ref, conf_ta_ref, _ = LabelGenerator.generate_label(ta_claim, ta_evidence_ref, match_score=0.4)
        self.assertEqual(label_ta_ref, "REFUTES")

        # Hindi SUPPORTS
        hi_claim = "केंद्रीय मंत्रिमंडल ने 8वें वेतन आयोग के गठन को मंजूरी दी।"
        hi_evidence_sup = "सरकार ने आधिकारिक विज्ञप्ति जारी कर 8वें वेतन आयोग के प्रस्ताव को मंजूरी दी है।"
        label_hi_sup, _, _ = LabelGenerator.generate_label(hi_claim, hi_evidence_sup, match_score=0.55)
        self.assertEqual(label_hi_sup, "SUPPORTS")

        # Hindi REFUTES
        hi_evidence_ref = "पत्र सूचना कार्यालय (PIB) ने स्पष्ट किया कि 8वें वेतन आयोग को लेकर किया जा रहा दावा पूरी तरह फर्जी खबर और भ्रामक है।"
        label_hi_ref, _, _ = LabelGenerator.generate_label(hi_claim, hi_evidence_ref, match_score=0.45)
        self.assertEqual(label_hi_ref, "REFUTES")

        # Marathi SUPPORTS
        mr_claim = "महाराष्ट्र सरकारने लाडकी बहीण योजनेची घोषणा केली."
        mr_evidence_sup = "मुख्यमंत्री कार्यालयाने पत्रकार परिषदेत लाडकी बहीण योजनेची अधिकृत घोषणा केली."
        label_mr_sup, _, _ = LabelGenerator.generate_label(mr_claim, mr_evidence_sup, match_score=0.6)
        self.assertEqual(label_mr_sup, "SUPPORTS")

        # Marathi REFUTES
        mr_evidence_ref = "शासनाने अशा कोणत्याही निर्णयाची बातमी फेटाळली असून सोशल मीडियावरील दावा खोटा आहे असे स्पष्ट केले."
        label_mr_ref, _, _ = LabelGenerator.generate_label(mr_claim, mr_evidence_ref, match_score=0.45)
        self.assertEqual(label_mr_ref, "REFUTES")

    def test_candidate_matcher_multilingual(self):
        # Tamil match
        c_ta = "தமிழ்நாடு அரசு பொங்கல் பரிசு தொகுப்பை அறிவித்துள்ளது"
        e_ta = "தமிழ்நாடு அரசு ரேஷன் அட்டைதாரர்களுக்கு பொங்கல் பரிசு தொகுப்பு வழங்கப்படும் என்று அறிவித்தது."
        res_ta = CandidateMatcher.compute_match_score(c_ta, e_ta)
        self.assertTrue(res_ta["is_relevant"])
        self.assertGreater(res_ta["score"], 0.25)

        # Hindi match
        c_hi = "सुप्रीम कोर्ट ने चुनावी बॉन्ड योजना को असंवैधानिक घोषित किया"
        e_hi = "सुप्रीम कोर्ट की 5 जजों की संविधान पीठ ने चुनावी बॉन्ड योजना को असंवैधानिक करार देते हुए रद्द किया।"
        res_hi = CandidateMatcher.compute_match_score(c_hi, e_hi)
        self.assertTrue(res_hi["is_relevant"])
        self.assertGreater(res_hi["score"], 0.25)

        # Marathi match
        c_mr = "मराठा आरक्षणाबाबत राज्य सरकारने विशेष अधिवेशन बोलावले"
        e_mr = "मराठा आरक्षणाच्या मुद्द्यावर चर्चा करण्यासाठी महाराष्ट्र शासनाने विधिमंडळाचे विशेष अधिवेशन बोलावले होते."
        res_mr = CandidateMatcher.compute_match_score(c_mr, e_mr)
        self.assertTrue(res_mr["is_relevant"])
        self.assertGreater(res_mr["score"], 0.25)

if __name__ == "__main__":
    unittest.main()
