# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
from difflib import SequenceMatcher


# Minimal stop words - keep domain-specific terms
skip_words = frozenset(
    {
        'the',
        'a',
        'an',
        'and',
        'or',
        'but',
        'in',
        'on',
        'at',
        'to',
        'for',
        'with',
        'by',
        'about',
        'as',
        'is',
        'are',
        'was',
        'were',
        'be',
        'been',
        'have',
        'has',
        'had',
        'do',
        'does',
        'did',
        'will',
        'would',
        'shall',
        'should',
        'can',
        'could',
        'may',
        'might',
        'must',
        'this',
        'that',
        'these',
        'those',
        'you',
        'your',
        'it',
        'its',
        'they',
        'them',
        'their',
    }
)


def _clean_text(text: str) -> str:
    """Clean and normalize text for comparison."""
    text = text.lower()
    text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
    text = re.sub(r'[^\w\s]', ' ', text)  # Remove punctuation
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    return text.strip()


def _extract_keywords(text: str) -> set[str]:
    """Extract meaningful keywords from text."""
    text = _clean_text(text)
    words = text.split()

    return {word for word in words if word and len(word) > 1 and word not in skip_words}


def calculate_similarity(query: str, operation_description: str) -> float:
    """Calculate similarity between query and operation description."""
    if not operation_description:
        return 0.0

    query_clean = _clean_text(query)
    clean_description = _clean_text(operation_description)

    if not query_clean or not clean_description:
        return 0.0

    query_keywords = _extract_keywords(query_clean)
    desc_keywords = _extract_keywords(clean_description)

    if not query_keywords:
        return 0.0

    keyword_overlap = len(query_keywords.intersection(desc_keywords))
    keyword_score = keyword_overlap / len(query_keywords)

    sequence_score = SequenceMatcher(None, query_clean, clean_description).ratio()

    # Look for exact phrase matches (higher weight)
    phrase_score = 0.0
    query_words = query_clean.split()
    for i in range(len(query_words)):
        for j in range(i + 2, min(i + 6, len(query_words) + 1)):  # 2-5 word phrases
            phrase = ' '.join(query_words[i:j])
            if phrase in clean_description:
                phrase_score = max(phrase_score, len(phrase.split()) / len(query_words))

    final_score = (keyword_score * 0.5) + (sequence_score * 0.3) + (phrase_score * 0.2)

    return min(final_score, 1.0)
