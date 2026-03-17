from coldmail.spam_check import check_spam


class TestCheckSpam:
    def test_clean_email(self):
        text = "Hi, I wanted to reach out about a potential collaboration."
        assert check_spam(text) == []

    def test_detects_single_spam_word(self):
        text = "This is a free consultation for you."
        found = check_spam(text)
        assert "free" in found

    def test_detects_multiple_spam_words(self):
        text = "Buy now and get a free trial with guaranteed results."
        found = check_spam(text)
        assert "buy" in found
        assert "free" in found
        assert "guaranteed" in found
        assert "trial" in found

    def test_case_insensitive(self):
        text = "ACT NOW for this AMAZING opportunity!"
        found = check_spam(text)
        assert "act now" in found
        assert "amazing" in found

    def test_whole_word_matching(self):
        """Should not match 'act' inside 'practice' or 'factor'."""
        text = "We practice good factors in our business."
        found = check_spam(text)
        assert "act" not in found

    def test_hyphenated_words(self):
        """Dashes should be treated as spaces for matching."""
        text = "This is a risk-free opportunity."
        found = check_spam(text)
        assert "risk free" in found

    def test_matches_js_behavior_sample_email(self):
        """Test against the same sample email from the JS file."""
        text = (
            "Hi Richie,\n\n"
            "My name is George, and I'm an AI consultant that helps small and midsize "
            "coaching businesses speed up content creation and client management by "
            "incorporating some of the latest AI technology.\n\n"
            "I'm interviewing leaders in the online coaching community about how they're "
            "using AI. If you're up for it, I would love to pick your brain for a few "
            "minutes, and I'll also send you an anonymized report summarizing my "
            "conversations with folks in your industry.\n\n"
            "Do you have 20 minutes for a quick, informal chat about how you're currently "
            "using AI?\n\n"
            "Have a great day,\n\nGeorge Norberg\nFounder\nPower Up Automations"
        )
        found = check_spam(text)
        # The JS version finds "community" doesn't match but "can i help" doesn't match.
        # This email is relatively clean — no spam words expected.
        assert found == []

    def test_no_duplicates_in_output(self):
        text = "Free free free! Buy buy buy!"
        found = check_spam(text)
        assert found.count("free") == 1
        assert found.count("buy") == 1

    def test_multiword_phrases(self):
        text = "You can earn extra cash with our amazing offer."
        found = check_spam(text)
        assert "earn extra cash" in found

    def test_empty_text(self):
        assert check_spam("") == []
