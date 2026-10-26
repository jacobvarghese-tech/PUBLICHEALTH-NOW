from __future__ import annotations
import unittest
from app.attachment import (attachment_notes, clean_npi, fields_from_attachment, gender_for_npi, parse_upload, roll_provider_rows)
from app.page_logic import FEATURE_FIELDS
CMS = 'Rndrng_NPI,Rndrng_Prvdr_Type,Rndrng_Prvdr_Gndr,Tot_Srvcs,Tot_Benes,Tot_Bene_Day_Srvcs,Avg_Sbmtd_Chrg,Avg_Mdcr_Pymt_Amt,year\n1124725817,Clinical Laboratory,,10,4,6,100,40,2024\n1639879034,Clinical Laboratory,,99,9,9,900,90,2024\n1124725817,Clinical Laboratory,,30,8,12,300,80,2024\n'

class AttachmentTests(unittest.TestCase):
    def test_roll_keeps_the_named_npi_and_fills_every_summary(self) -> 'None':
        fields = roll_provider_rows(CMS, '1124725817', 2024)
        self.assertEqual(fields['Specialty'], 'Clinical Laboratory')
        self.assertEqual(fields['line_srvc_cnt_mean'], '20')
        self.assertEqual(fields['line_srvc_cnt_sum'], '40')
        self.assertEqual(fields['line_srvc_cnt_min'], '10')
        self.assertEqual(fields['line_srvc_cnt_max'], '30')
        self.assertEqual(fields['average_submitted_chrg_amt_sum'], '400')
        self.assertIsNone(roll_provider_rows(CMS, '0000000001', 2024))

    def test_year_filter_skips_another_year(self) -> 'None':
        text = CMS.replace(',2024', ',2023')
        self.assertIsNone(roll_provider_rows(text, '1124725817', 2024))
        kept = roll_provider_rows(text, '1124725817', 2023)
        self.assertEqual(kept['line_srvc_cnt_sum'], '40')

    def test_bad_npi_is_rejected_before_a_model_call(self) -> 'None':
        with self.assertRaises(ValueError):
            clean_npi('123')
        with self.assertRaises(ValueError):
            fields_from_attachment('notes.txt', b'Clinical Laboratory', '12', None, client=object())

    def test_prose_attachment_asks_only_for_that_provider(self) -> 'None':
        calls = []
        class Client:
            responses = None
            def create(self, **kwargs):
                calls.append(kwargs)
                return type('Response', (), {'output_text': '{"Specialty":"Clinical Laboratory"}'})()


        client = Client()
        client.responses = client
        fields = fields_from_attachment('tip.txt', b'NPI 1124725817 is a clinical laboratory. Services mean 12.', '1124725817', 2024, client=client)
        self.assertEqual(fields['Specialty'], 'Clinical Laboratory')
        self.assertEqual(len(calls), 1)
        prompt = calls[0]['input'][1]['content']
        self.assertIn('NPI 1124725817', prompt)
        self.assertIn('that provider only', prompt)
        self.assertIsNone(fields['line_srvc_cnt_mean'])
        self.assertEqual(set(fields), set(FEATURE_FIELDS))

    def test_multipart_reads_the_attachment_and_rejects_an_empty_one(self) -> 'None':
        body = b'--bound\r\nContent-Disposition: form-data; name="attachment"; filename="rows.csv"\r\nContent-Type: text/csv\r\n\r\nnpi,line_srvc_cnt\r\n1124725817,10\r\n--bound--\r\n'
        filename, payload = parse_upload('multipart/form-data; boundary=bound', body)
        self.assertEqual(filename, 'rows.csv')
        self.assertIn(b'1124725817', payload)
        empty = body.replace(b'npi,line_srvc_cnt\r\n1124725817,10\r\n', b'')
        with self.assertRaises(ValueError):
            parse_upload('multipart/form-data; boundary=bound', empty)

    def test_binary_name_is_not_decoded_as_notes(self) -> 'None':
        notes = attachment_notes('scan.pdf', b'%PDF-1.4')
        self.assertEqual(notes, 'Attachment name: scan.pdf')

    def test_gender_lookup_stops_at_a_known_npi(self) -> 'None':
        gender = gender_for_npi('1124725817')
        self.assertIn(gender, ('', 'M', 'F'))


if __name__ == '__main__':
    unittest.main()
