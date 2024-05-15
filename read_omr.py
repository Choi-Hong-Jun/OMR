import os
import json
import fitz
import cv2
import numpy as np


class OMRReader:
    def __init__(self, f_pdf, class_name, item_name) -> None:
        assert os.path.exists(f_pdf), f'no such file {f_pdf}'

        self.pdf_filename = f_pdf
        self.class_name = class_name
        self.item_name = item_name

        self.pdf_document = fitz.open(self.pdf_filename)
        self.nr_pages = len(self.pdf_document)
        self.all_img_path = list()

        with open('korean_data.json', encoding='utf-8') as f:
            self.map_kor = json.load(f)

    def convert_pdf_to_png(self):
        for page_number in range(len(self.pdf_document)):
            page = self.pdf_document.load_page(page_number)
            pix = page.get_pixmap()
            img_path = f"{self.item_name}_{self.class_name}_page{page_number + 1}.png"
            pix.save(img_path)

            self.all_img_path.append(img_path)
            # self.extract_data(img_path)

    def extract_data(self, img_path):
        img, gray = self.read_img_with_cv_as_gray(img_path)

        _name = self.extract_name(img, gray)
        _number = self.extract_number(img, gray)
        _answer = self.extract_omr(img, gray)

    def extract_name(self, img, gray):   # omr 이름 표에 삽입
        fullname = list()
        self.colored = list()

        fullname.append(self.extract_each_name(img, gray, [
            ((183, 277, 17, 200), self.map_kor['jamo1'], 210),
            ((199, 277, 17, 266), self.map_kor['jamo2'], 200),
            ((215, 277, 17, 200), self.map_kor['jamo1'], 210),
        ]))

        fullname.append(self.extract_each_name(img, gray, [
            ((234, 277, 17, 200), self.map_kor['jamo1'], 210),
            ((250, 277, 17, 266), self.map_kor['jamo2'], 200),
            ((266, 277, 17, 200), self.map_kor['jamo1'], 210),
        ]))

        fullname.append(self.extract_each_name(img, gray, [
            ((285, 277, 17, 200), self.map_kor['jamo1'], 210),
            ((300, 277, 17, 266), self.map_kor['jamo2'], 200),
            ((314, 277, 17, 200), self.map_kor['jamo1'], 210),
        ]))

        fullname = ''.join(fullname)
        return fullname

    def extract_each_name(self, img, gray, cmt):
        omr_names = list()
        for (coordinates, _map, threshold), _type in zip(cmt, ['cho', 'jung', 'jong']):
            omr_names.append(self._extract_name(img, gray, coordinates, _map, threshold, _type))

        return self.get_a_korean_ascii(omr_names)

    def get_a_korean_ascii(self, names):
        assert len(names) == 3, f'each Korean has 3 parts: {names}'

        HANGUL_START = 0xAC00

        try:
            if names[0] not in self.map_kor['cho']:
                raise ValueError(f"초성 '{names[0]}' is not valid.")
            if names[1] not in self.map_kor['jung']:
                raise ValueError(f"중성 '{names[1]}' is not valid.")
            if names[2] and names[2] not in self.map_kor['jong']:
                raise ValueError(f"종성 '{names[2]}' is not valid.")

            cho_index = self.map_kor['cho'].index(names[0])
            jung_index = self.map_kor['jung'].index(names[1])
            jong_index = self.map_kor['jong'].index(names[2]) if names[2] else 0

            code_point = (cho_index * len(self.map_kor['jung']) * len(self.map_kor['jong']))
            code_point += (jung_index * len(self.map_kor['jong']))
            code_point += jong_index + HANGUL_START

            return chr(code_point)
        except ValueError as e:
            print(f'## Exception: {str(e)}')
            return ''

    def _extract_name(self, img, gray, user_coordinates, _map, threshold, _type):
        x, y, w, h = user_coordinates
        question_img = gray[y:y + h, x:x + w]
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

        rawdat = list()
        for i in range(len(_map)):
            start_y = int(h * i / len(_map))
            end_y = int(h * (i + 1) / len(_map))
            choice_img = question_img[start_y:end_y, :]
            avg_pixel_value = int(np.mean(choice_img))

            rawdat.append(avg_pixel_value)

        mean_colored = 0
        if self.colored:
            mean_colored = int(np.mean(self.colored))

        ret = self.select_filled_loc(rawdat, threshold, mean_colored)

        chosen = None
        if len(ret['index_under_threshold']) == 1:
            chosen = ret['index_under_threshold'][0]
        elif ret['index_min'] in ret['index_under_threshold'] or\
             ret['index_min'] in ret['index_under_threshold2']:
            chosen = ret['index_min']
        elif (not ret['index_under_threshold'] and not ret['index_under_threshold2']) and\
             _type in ['cho', 'jung']:
            chosen = ret['index_min']

        if chosen != None:
            print(f'* {_map[chosen]} {rawdat[chosen]} / [{threshold},{mean_colored}] {rawdat} / {ret}')
            self.colored.append(rawdat[chosen])
            return _map[chosen]
        else:
            print(f'# [{threshold},{mean_colored}] {rawdat} / {ret}')
        
    def select_filled_loc(self, rawdat, threshold, threshold2=None):
        # how to distinguish efficiently? normalization ?
        # normdat = [round(float(i)/sum(rawdat)*100, 2) for i in rawdat]
        under_1 = list()
        under_2 = list()
        for i, d in enumerate(rawdat):
            if d < threshold:
                under_1.append(i)
            if threshold2 and d < threshold2:
                under_2.append(i)

        return {
            'index_min' : rawdat.index(np.min(rawdat)),
            'index_under_threshold' : under_1,
            'index_under_threshold2' : under_2,
        }

    def extract_number(self, img, gray):   # omr 학번 표에 삽입
        omr_numbers = []
        user_coordinates = [
            (99, 270, 11, 245),
            (113, 270, 11, 245),
            (127, 270, 11, 245),
            (142, 270, 11, 245)
        ]
        threshold = 210

        for coordinates in user_coordinates:
            x, y, w, h = coordinates
            question_img = gray[y:y + h, x:x + w]

            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            choices = []
            for i in range(10):
                start_y = int(h * i / 10)
                end_y = int(h * (i + 1) / 10)
                choice_img = question_img[start_y:end_y, :]
                avg_pixel_value = np.mean(choice_img)

                if avg_pixel_value < threshold:
                    choices.append(i)

            omr_numbers.append(choices)

        return int(''.join(str(num[0]) if num else '0' for num in omr_numbers))

    def extract_omr(self, img, gray):   # omr 답 표에 삽입
        omr_answers = []
        user_coordinates = [(422, 75, 78, 22), (422, 100, 78, 22), (422, 125, 78, 22), (422, 149, 78, 22), (422, 172, 78, 22),
                            (422, 197, 78, 22), (422, 220, 78, 22), (422, 245, 78, 22), (422, 270, 78, 22), (422, 293, 78, 22),
                            (422, 318, 78, 22), (422, 341, 78, 22), (422, 365, 78, 22), (422, 390, 78, 22), (422, 413, 78, 22),
                            (422, 438, 78, 22), (422, 461, 78, 22), (422, 486, 78, 22), (422, 510, 78, 22), (422, 535, 78, 22),
                            (557, 75, 78, 22), (557, 100, 78, 22), (557, 125, 78, 22), (557, 150, 78, 22), (557, 172, 78, 22),
                            (557, 197, 78, 22), (557, 220, 78, 22), (557, 245, 78, 22), (557, 270, 78, 22), (557, 293, 78, 22),
                            (557, 318, 78, 22), (557, 340, 78, 22), (557, 365, 78, 22), (557, 390, 78, 22), (557, 413, 78, 22),
                            (557, 438, 78, 22), (557, 461, 78, 22), (557, 485, 78, 22), (557, 510, 78, 22), (557, 535, 78, 22),
                            (693, 75, 78, 22), (693, 100, 78, 22), (693, 125, 78, 22), (693, 150, 78, 22), (693, 172, 78, 22),
                            (693, 197, 78, 22), (693, 221, 78, 22), (693, 246, 78, 22), (693, 270, 78, 22), (693, 293, 78, 22),
                            (693, 318, 78, 22), (693, 342, 78, 22), (693, 365, 78, 22), (693, 390, 78, 22), (693, 413, 78, 22),
                            (693, 438, 78, 22), (693, 461, 78, 22), (693, 486, 78, 22), (693, 510, 78, 22), (693, 535, 78, 22)]

        num_questions = 0
        if self.item_name:
            file_name = f"{self.item_name}_table_data.json"
            if os.path.exists(file_name):
                with open(file_name, "r", encoding='utf-8') as json_file:
                    data = json.load(json_file)

                    if isinstance(data, list):
                        num_questions = len(data)
                    elif isinstance(data, dict) and "num_questions" in data:
                        num_questions = data["num_questions"]
                    else:
                        return

        else:
            print('## No Item Name, Quit')
            return

        desired_coordinates_count = int(num_questions)
        threshold = 225
        for question_idx, coordinates in enumerate(user_coordinates):
            if question_idx >= desired_coordinates_count:
                break

            x, y, w, h = coordinates
            question_img = gray[y:y + h, x:x + w]
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            choices = []
            for j in range(5):
                start_x = int(w * j / 5)
                end_x = int(w * (j + 1) / 5)
                choice_img = question_img[:, start_x:end_x]
                avg_pixel_value = np.mean(choice_img)

                if avg_pixel_value < threshold:
                    choices.append(str(j + 1))

            omr_answers.append(choices)

        return omr_answers
    
    def read_img_with_cv(self, img_path):
        img_array = np.fromfile(img_path, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        # assert img, f'fail to read img {img_path}'
        return img

    def read_img_with_cv_as_gray(self, img_path):
        img = self.read_img_with_cv(img_path)
        return img, cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


if __name__ == '__main__':
    f_pdf = 'OMR 예시.pdf'
    o = OMRReader(f_pdf, 'no_class', 'no_item')
    o.convert_pdf_to_png()
    for f in o.all_img_path:
        img, gray_img = o.read_img_with_cv_as_gray(f)

        _name = o.extract_name(img, gray_img)
        _num = o.extract_number(img, gray_img)
        _ans = o.extract_omr(img, gray_img)

        print(f'{f}: {_name} / {_num} / {_ans}')
