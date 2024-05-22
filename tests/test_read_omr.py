import json
import unittest
import os
import sys
TESTDIR = os.path.dirname(os.path.abspath(__file__))
ROOTDIR = os.path.dirname(TESTDIR)
sys.path.append(ROOTDIR)

from read_omr import OMRReader

class TestOMRReader(unittest.TestCase):
    skip_sample = [
        '/Users/jinho/Documents/OMR/tests/samples/20240419185025.pdf'
    ]

    def setUp(self):
        with open(os.path.join(TESTDIR, 'samples', 'answer.json')) as f:
            self.answer = json.load(f)

    def test_all_samples(self):
        dir_samples = os.path.join(TESTDIR, 'samples')
        all_pdf = list()
        for each in os.listdir(dir_samples):
            if each.endswith('.pdf'):
                all_pdf.append(os.path.join(dir_samples, each))

        all_result = list()
        th = 5
        for index, each in enumerate(all_pdf):
            if each in self.skip_sample: continue

            print(f'# handle: {each}')
            o = OMRReader(each, None, None)
            o.convert_pdf_to_png()
            for f in o.all_img_path:
                o.extract_data(f)

            all_result.append(o.raw_answer)

            # if th < index:
            #     break

        self.make_score(all_result)

        with open('result.json', 'w') as f:
            json.dump(all_result, f, indent=4)

        with open('result_orig.json') as f:
            all_result_orig = json.load(f)

        self.assertEqual(all_result, all_result_orig)

    def make_score(self, current):
        hit = 0
        missed = 0
        for each in current:
            fname = os.path.basename(each['f_pdf'])
            if fname not in self.answer: continue

            answer = self.answer[fname]
            for c, a in zip(each['data'], answer):
                for n_c, n_a in zip(c['number']['colored'], a['number']):
                    if n_c == n_a:
                        hit += 1
                    else:
                        missed += 1

                for n_c, n_a in zip(c['answer']['colored'], a['answer']):
                    if n_c == n_a:
                        hit += 1
                    else:
                        missed += 1

        print(f'# hit: {hit}, missed: {missed} / {hit + missed}')
