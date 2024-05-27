import json
import unittest
import os
import numpy as np
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
        th = 999
        print(f'# total samples: {len(all_pdf)}, answers: {len(self.answer)}')
        for index, each in enumerate(all_pdf):
            if each in self.skip_sample: continue

            found = False
            for a in self.answer.keys():
                if os.path.basename(each) == a:
                    found = True
                    break

            if not found:
                print(f'# skip: {each}')
                continue

            print(f'# handle: {each}')
            o = OMRReader(each, None, None)
            o.convert_pdf_to_png()
            for f in o.all_img_path:
                o.extract_data(f)

            all_result.append(o.raw_answer)

            if th < index:
                print(f'# break at {index}')
                break

        self.make_score(all_result)

        with open('result.json', 'w') as f:
            json.dump(all_result, f, indent=4)
        return

        with open('result_orig.json') as f:
            all_result_orig = json.load(f)

        self.assertEqual(all_result, all_result_orig)

    def make_score(self, current):
        print(f'\n\n{"-"*50}\n\n')
        hit = 0
        missed = 0
        for each in current:
            fname = os.path.basename(each['f_pdf'])
            if fname not in self.answer: continue

            answer = self.answer[fname]
            for nr_page, (c, a) in enumerate(zip(each['data'], answer), start=1):
                for key in ['number', 'answer']:
                    fixed = 0
                    if key == 'answer':
                        fixed = 1

                    for i, (n_c, n_a) in enumerate(zip(c[key]['colored'], a[key])):
                        if n_c == n_a:
                            hit += 1
                        else:
                            missed += 1
                            min_loc = c[key]["raw"][i].index(np.min(c[key]["raw"][i]))
                            print(f'{fname}:{nr_page:<2} {a["name"]} {key:6}:{i+fixed:>2} -> {n_c} != {n_a}: {c[key]["raw"][i]} ({min_loc + fixed})', end='')

                            matching_val = min_loc + fixed
                            if key == 'answer':
                                matching_val = [matching_val]

                            if n_a != matching_val:
                                print(f' -> "NOT minimum rawdat"')
                            else:
                                print('')

                            o = OMRReader(each['f_pdf'], None, None, True)
                            o.select_filled_loc_without_threshold(c[key]["raw"][i])
                            print(f'{"+"*50}\n\n')

        print(f'\n# SCORE: [{round(hit/(hit+missed)*100, 2)}] {hit}/{missed}')
