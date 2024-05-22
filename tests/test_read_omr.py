import json
import unittest
import os
import sys
TESTDIR = os.path.dirname(os.path.abspath(__file__))
ROOTDIR = os.path.dirname(TESTDIR)
sys.path.append(ROOTDIR)

from read_omr import OMRReader

class TestOMRReader(unittest.TestCase):
    def test_all_samples(self):
        dir_samples = os.path.join(TESTDIR, 'samples')
        all_pdf = list()
        for each in os.listdir(dir_samples):
            if each.endswith('.pdf'):
                all_pdf.append(os.path.join(dir_samples, each))

        all_result = list()
        th = 5
        for index, each in enumerate(all_pdf):
            print(f'# handle: {each}')
            o = OMRReader(each, None, None)
            o.convert_pdf_to_png()
            for f in o.all_img_path:
                o.extract_data(f)

            all_result.append(o.raw_answer)

            if th < index:
                break

        with open('result.json', 'w') as f:
            json.dump(all_result, f, indent=4)

        with open('result_orig.json') as f:
            all_result_orig = json.load(f)

        self.assertEqual(all_result, all_result_orig)

