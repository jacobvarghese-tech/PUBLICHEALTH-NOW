from __future__ import annotations
import unittest
from app.extract import (MISSING_KEY_MESSAGE, clean_fields, extract_fields, extract_schema, parse_model_json)

class FakeResponse:
    def __init__(self, text: 'str') -> 'None':
        self.output_text = text


class FakeClient:
    def __init__(self, text: 'str') -> 'None':
        self.text = text
        self.calls = []
        self.responses = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return FakeResponse(self.text)


class ExtractTests(unittest.TestCase):
    def test_search_cleanup_keeps_only_written_fields(self) -> 'None':
        cleaned = clean_fields('search', {'query': ' Prince Laboratories ', 'year': 'billed in 2024'})
        self.assertEqual(cleaned['query'], 'Prince Laboratories')
        self.assertEqual(cleaned['year'], '2024')
        blank = clean_fields('search', {'query': None, 'year': '1999'})
        self.assertIsNone(blank['query'])
        self.assertIsNone(blank['year'])

    def test_model_cleanup_drops_invented_text_and_keeps_numbers(self) -> 'None':
        cleaned = clean_fields('model', {'Specialty': 'Clinical Laboratory', 'Gender': '', 'line_srvc_cnt_mean': '$1,240.50', 'line_srvc_cnt_sum': 'not stated'})
        self.assertEqual(cleaned['Specialty'], 'Clinical Laboratory')
        self.assertIsNone(cleaned['Gender'])
        self.assertEqual(cleaned['line_srvc_cnt_mean'], '1240.5')
        self.assertIsNone(cleaned['line_srvc_cnt_sum'])
        self.assertIsNone(cleaned['average_medicare_payment_amt_max'])

    def test_schema_requires_every_score_field(self) -> 'None':
        schema = extract_schema('model')
        self.assertEqual(schema['additionalProperties'], False)
        self.assertIn('Specialty', schema['required'])
        self.assertIn('average_medicare_payment_amt_max', schema['required'])

    def test_extract_uses_the_responses_sample_and_does_not_need_a_live_key(self) -> 'None':
        client = FakeClient('{"query":"Deerfield Beach","year":"2024"}')
        fields = extract_fields('search', 'Deerfield Beach in 2024', client=client)
        self.assertEqual(fields['query'], 'Deerfield Beach')
        call = client.calls[0]
        self.assertEqual(call['model'], 'grok-4.7')
        self.assertEqual(call['text']['format']['type'], 'json_schema')
        self.assertEqual(call['input'][1]['content'], 'Deerfield Beach in 2024')

    def test_empty_notes_do_not_call_the_model(self) -> 'None':
        with self.assertRaises(ValueError):
            extract_fields('search', '   ', client=FakeClient('{}'))

    def test_missing_key_message_is_stable(self) -> 'None':
        self.assertIn('XAI_API_KEY', MISSING_KEY_MESSAGE)

    def test_parse_rejects_prose_without_fields(self) -> 'None':
        with self.assertRaises(ValueError):
            parse_model_json('I could not find a provider.')


if __name__ == '__main__':
    unittest.main()
