import os
import json
import cv2
import fitz
import numpy as np
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QFileDialog, QTableWidget,
                             QLabel, QLineEdit, QTableWidgetItem, QComboBox, QStackedWidget)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt
from read_omr import OMRReader

class OMRGradingWidget(QWidget):    # OMR 채점 화면

    def __init__(self):
        super().__init__()
        self.initUI()
        self.loadItems()

    def initUI(self):
        self.setWindowTitle('OMR 채점 화면')
        self.setWindowIcon(QIcon('logo.jpeg'))
        self.showFullScreen()

        btn = QPushButton('메인 화면', self)
        btn1 = QPushButton('시험 입력', self)
        btn2 = QPushButton('OMR 채점', self)
        btn3 = QPushButton('성적표 인쇄', self)
        self.btn4 = QPushButton('파일 선택', self)
        self.btn5 = QPushButton('결과 저장', self)
        btn.setFixedSize(120, 40)
        btn1.setFixedSize(120, 40)
        btn2.setFixedSize(120, 40)
        btn3.setFixedSize(120, 40)
        self.btn4.setFixedSize(100, 40)
        self.btn5.setFixedSize(100, 40)
        self.btn4.move(20, 700)
        self.btn5.move(120, 700)
        self.btn4.clicked.connect(self.uploadFile)
        self.btn5.clicked.connect(self.saveScore)
        self.btn4.show()
        self.btn5.show()

        self.lbl = QLabel('학급명', self)
        self.lbl.setGeometry(25, 650, 150, 30)
        self.lbl.show()

        self.line_edit = QLineEdit(self)
        self.line_edit.setGeometry(75, 650, 100, 30)
        self.line_edit.show()

        vbox = QVBoxLayout()
        vbox.addWidget(btn)
        vbox.addWidget(btn1)
        vbox.addWidget(btn2)
        vbox.addWidget(btn3)
        vbox.addStretch()

        self.setLayout(vbox)

        self.label = QLabel('시험 선택', self)
        self.label.setGeometry(190, 20, 200, 50)
        self.label.show()

        self.cb = QComboBox(self)   # 시험지 항목 콤보 박스 생성
        self.cb.setGeometry(280, 30, 160, 30)
        self.cb.activated.connect(self.updateCol)
        self.cb.activated.connect(self.load_answer)
        self.cb.show()

        self.table_widget = QTableWidget(self)
        self.table_widget.setRowCount(1)
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(["이름", "학번", "학급명", "점수"])
        self.table_widget.setGeometry(180, 70, 1500, 350)
        self.table_widget.itemChanged.connect(self.updateTotalScore)
        self.table_widget.show()

        btn.clicked.connect(self.showMainWidget)
        btn1.clicked.connect(self.showExamInputWidget)
        btn3.clicked.connect(self.showSendReportWidget)

        self.stacked_widget = QStackedWidget(self)   # pdf 파일 출력 다중 페이지 어플 생성
        self.stacked_widget.setGeometry(500, 420, 1000, 600)

        self.btn_prevpage = QPushButton("이전 화면", self)
        self.btn_nextpage = QPushButton("다음 화면", self)
        self.btn_prevpage.setFixedSize(80, 40)
        self.btn_nextpage.setFixedSize(80, 40)
        self.btn_prevpage.move(900, 1020)
        self.btn_nextpage.move(980, 1020)

        self.btn_prevpage.clicked.connect(self.previousPage)
        self.btn_nextpage.clicked.connect(self.nextPage)

        self.stacked_widget.show()
        self.show()

    def loadItems(self):   # 콤보 박스의 항목 정보 불러오기
        self.cb.addItem("")
        if os.path.exists("list_items.txt"):
            with open("list_items.txt", "r", encoding="utf-8") as file:
                items = file.readlines()
                self.cb.addItems(item.strip() for item in items)

    def updateCol(self):   # 표의 열 수 조정
        selected_item = self.cb.currentText()
        if selected_item:
            file_name = f"{selected_item}_table_data.json"
            if os.path.exists(file_name):
                with open(file_name, "r", encoding='utf-8') as json_file:
                    data = json.load(json_file)

                    num_questions = data.get("num_questions", 0)

                    if isinstance(num_questions, str) and num_questions.isdigit():
                        num_questions = int(num_questions)

                    col_count = num_questions + 4 if isinstance(num_questions, int) else 4

                    self.table_widget.setColumnCount(col_count)

                    headers = ["이름", "학번", "학급명", "점수"]
                    for i in range(4, col_count):
                        headers.append(str(i - 3))
                    self.table_widget.setHorizontalHeaderLabels(headers)

                    for column in range(4, col_count):
                        if str(column - 3).isdigit():
                            self.table_widget.setColumnWidth(column, 50)

    def updateRow(self, row_count):  # 표의 행 수 조정
        self.table_widget.setRowCount(row_count)

        for row_index in range(row_count):   # 학급명 표에 입력
            text = self.line_edit.text()
            item = QtWidgets.QTableWidgetItem(text)
            self.table_widget.setItem(row_index, 2, item)
            item.setTextAlignment(Qt.AlignCenter)

    def uploadFile(self):  # 파일 찾기
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*);;Text Files (*.txt)")

        assert os.path.exists(file_path), f'no such {file_path}'

        self.omr_reader = OMRReader(file_path, self.line_edit.text(), self.cb.currentText())
        self.omr_reader.convert_pdf_to_png()
        nr_pages = len(self.omr_reader.all_img_path)

        # update row with number of pages in pdf
        self.updateRow(nr_pages)

        for each_file in self.omr_reader.all_img_path:
            img, gray_img = self.omr_reader.read_img_with_cv_as_gray(each_file)

            self.addPageToStackedWidget(each_file)

            _name = self.omr_reader.extract_name(img, gray_img)
            self.update_name(_name)

            _num = self.omr_reader.extract_number(img, gray_img)
            self.update_number(_num)

            _ans = self.omr_reader.extract_omr(img, gray_img)
            self.omr_grading(_ans)
            self.update_answer(_ans)

        if nr_pages > 1:
            self.btn_prevpage.show()
            self.btn_nextpage.show()
        else:
            self.btn_prevpage.hide()
            self.btn_nextpage.hide()

        # if file_path:
        #     pdf_document = fitz.open(file_path)
        #     self.pdf_to_png(pdf_document)

    def update_name(self, one_name):
        current_row = 0
        while current_row < self.table_widget.rowCount():
            item = self.table_widget.item(current_row, 0)
            if item is None or item.text() == '':
                item = QTableWidgetItem(one_name)
                self.table_widget.setItem(current_row, 0, item)
                item.setTextAlignment(Qt.AlignCenter)
                break
            current_row += 1

        # Refactoring example
        #
        # for row_index in range(self.table_widget.rowCount()):
        #     item = self.table_widget.item(row_index, 0)
        #     if not item or not item.text():
        #         item = QTableWidgetItem(one_name)
        #         self.table_widget.setItem(row_index, 0, item)
        #         item.setTextAlignment(Qt.AlignCenter)
        #         break

    def update_number(self, num):
        while current_row < self.table_widget.rowCount():
            item = self.table_widget.item(current_row, 1)
            if item is None or item.text() == '':
                item = QTableWidgetItem(str(num))
                self.table_widget.setItem(current_row, 1, item)
                item.setTextAlignment(Qt.AlignCenter)
                break
            current_row += 1

    def update_answer(self, ans):
        for column_idx, column_answers in enumerate(ans, start=4):
            row_index = 0
            for choice in column_answers:
                current_item = self.table_widget.item(row_index, column_idx)
                if current_item is None or current_item.text() == "":
                    item = QTableWidgetItem(str(choice))
                    self.table_widget.setItem(row_index, column_idx, item)
                    item.setTextAlignment(Qt.AlignCenter)
                else:
                    while True:
                        row_index += 1
                        if row_index >= self.table_widget.rowCount():
                            break
                        if self.table_widget.item(row_index, column_idx) is None or\
                            self.table_widget.item(row_index, column_idx).text() == "":
                            break
                    if row_index < self.table_widget.rowCount():
                        item = QTableWidgetItem(str(choice))
                        self.table_widget.setItem(row_index, column_idx, item)
                        item.setTextAlignment(Qt.AlignCenter)
    
    def pdf_to_png(self, pdf_document):  # pdf 파일 png 파일로 변환
        class_name = self.line_edit.text()
        selected_item = self.cb.currentText()
        row_count = len(pdf_document) if pdf_document else 0
        self.updateRow(row_count)

        for page_number in range(len(pdf_document)):
            page = pdf_document.load_page(page_number)
            pix = page.get_pixmap()
            img_path = f"{selected_item}_{class_name}_page{page_number + 1}.png"
            pix.save(img_path)
            self.addPageToStackedWidget(img_path)
            self.extract_name(img_path)
            self.extract_number(img_path)
            self.extract_omr(img_path)

        if len(pdf_document) > 1:
            self.btn_prevpage.show()
            self.btn_nextpage.show()
        else:
            self.btn_prevpage.hide()
            self.btn_nextpage.hide()

    def extract_name1_1(self, img_path):  # 이름 첫번째 글자의 초성
        img = self.read_img_with_cv(img_path)
        if img is None:
            print("")
            return

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        omr_names = []
        user_coordinates = [(183, 277, 17, 200)]

        for coordinates in user_coordinates:
            x, y, w, h = coordinates
            question_img = gray[y:y + h, x:x + w]
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            choices = []

            hangul_jamo_map = {
                0: 'ㄱ',
                1: 'ㄴ',
                2: 'ㄷ',
                3: 'ㄹ',
                4: 'ㅁ',
                5: 'ㅂ',
                6: 'ㅅ',
                7: 'ㅇ',
                8: 'ㅈ',
                9: 'ㅊ',
                10: 'ㅋ',
                11: 'ㅌ',
                12: 'ㅍ',
                13: 'ㅎ'
            }

            for i in range(14):
                start_y = int(h * i / 14)
                end_y = int(h * (i + 1) / 14)
                choice_img = question_img[start_y:end_y, :]
                avg_pixel_value = np.mean(choice_img)

                if avg_pixel_value < 210:
                    choices.append(hangul_jamo_map[i])
            omr_names.append(''.join(choices))
        return omr_names

    def extract_name1_2(self, img_path):   # 이름 첫번째 글자의 중성
        img = self.read_img_with_cv(img_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        omr_names = []
        user_coordinates = [(199, 277, 17, 266)]

        for coordinates in user_coordinates:
            x, y, w, h = coordinates
            question_img = gray[y:y + h, x:x + w]
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            choices = []
            hangul_jamo_map = {
                0: 'ㅏ',
                1: 'ㅑ',
                2: 'ㅓ',
                3: 'ㅕ',
                4: 'ㅗ',
                5: 'ㅛ',
                6: 'ㅜ',
                7: 'ㅠ',
                8: 'ㅡ',
                9: 'ㅣ',
                10: 'ㅐ',
                11: 'ㅒ',
                12: 'ㅔ',
                13: 'ㅖ',
                14: 'ㅘ',
                15: 'ㅚ',
                16: 'ㅝ',
                17: 'ㅟ',
                18: 'ㅢ'
            }

            for i in range(19):
                start_y = int(h * i / 19)
                end_y = int(h * (i + 1) / 19)
                choice_img = question_img[start_y:end_y, :]
                avg_pixel_value = np.mean(choice_img)

                if avg_pixel_value < 200:
                    choices.append(hangul_jamo_map[i])
            omr_names.append(''.join(choices))
        return omr_names

    def extract_name1_3(self, img_path):   # 이름 첫번째 글자의 종성
        img = self.read_img_with_cv(img_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        omr_names = []
        user_coordinates = [(215, 277, 17, 200)]

        for coordinates in user_coordinates:
            x, y, w, h = coordinates
            question_img = gray[y:y + h, x:x + w]
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            choices = []
            hangul_jamo_map = {
                0: 'ㄱ',
                1: 'ㄴ',
                2: 'ㄷ',
                3: 'ㄹ',
                4: 'ㅁ',
                5: 'ㅂ',
                6: 'ㅅ',
                7: 'ㅇ',
                8: 'ㅈ',
                9: 'ㅊ',
                10: 'ㅋ',
                11: 'ㅌ',
                12: 'ㅍ',
                13: 'ㅎ'
            }

            for i in range(14):
                start_y = int(h * i / 14)
                end_y = int(h * (i + 1) / 14)
                choice_img = question_img[start_y:end_y, :]
                avg_pixel_value = np.mean(choice_img)

                if avg_pixel_value < 210:
                    choices.append(hangul_jamo_map[i])
            omr_names.append(''.join(choices))
        return omr_names

    def extract_name1(self, img_path):   # 이름 첫번째 글자
        HANGUL_START = 0xAC00

        cho_list = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']

        jung_list = ['ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ',
                     'ㅣ']

        jong_list = [''] + ['ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ',
                            'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']

        omr_names_1 = self.extract_name1_1(img_path)
        omr_names_2 = self.extract_name1_2(img_path)
        omr_names_3 = self.extract_name1_3(img_path)

        combined_names = []

        for idx, (omr_name_1, omr_name_2, omr_name_3) in enumerate(zip(omr_names_1, omr_names_2, omr_names_3)):
            try:
                if omr_name_1 not in cho_list:
                    raise ValueError(f"초성 '{omr_name_1}' at index {idx} is not valid.")
                if omr_name_2 not in jung_list:
                    raise ValueError(f"중성 '{omr_name_2}' at index {idx} is not valid.")
                if omr_name_3 and omr_name_3 not in jong_list:
                    raise ValueError(f"종성 '{omr_name_3}' at index {idx} is not valid.")

                cho_index = cho_list.index(omr_name_1)
                jung_index = jung_list.index(omr_name_2)
                jong_index = jong_list.index(omr_name_3) if omr_name_3 else 0

                code_point = (cho_index * len(jung_list) * len(jong_list)) + (
                            jung_index * len(jong_list)) + jong_index + HANGUL_START
                combined_names.append(chr(code_point))
            except ValueError as e:
                continue

        return combined_names

    def extract_name2_1(self, img_path):   # 이름 두번째 글자의 초성
        img = self.read_img_with_cv(img_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        omr_names = []
        user_coordinates = [(234, 277, 17, 200)]

        for coordinates in user_coordinates:
            x, y, w, h = coordinates
            question_img = gray[y:y + h, x:x + w]
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            choices = []
            hangul_jamo_map = {
                0: 'ㄱ',
                1: 'ㄴ',
                2: 'ㄷ',
                3: 'ㄹ',
                4: 'ㅁ',
                5: 'ㅂ',
                6: 'ㅅ',
                7: 'ㅇ',
                8: 'ㅈ',
                9: 'ㅊ',
                10: 'ㅋ',
                11: 'ㅌ',
                12: 'ㅍ',
                13: 'ㅎ'
            }

            for i in range(14):
                start_y = int(h * i / 14)
                end_y = int(h * (i + 1) / 14)
                choice_img = question_img[start_y:end_y, :]
                avg_pixel_value = np.mean(choice_img)

                if avg_pixel_value < 210:
                    choices.append(hangul_jamo_map[i])
            omr_names.append(''.join(choices))
        return omr_names

    def extract_name2_2(self, img_path):   # 이름 두번째 글자의 중성
        img = self.read_img_with_cv(img_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        omr_names = []
        user_coordinates = [(250, 277, 17, 266)]

        for coordinates in user_coordinates:
            x, y, w, h = coordinates
            question_img = gray[y:y + h, x:x + w]
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            choices = []
            hangul_jamo_map = {
                0: 'ㅏ',
                1: 'ㅑ',
                2: 'ㅓ',
                3: 'ㅕ',
                4: 'ㅗ',
                5: 'ㅛ',
                6: 'ㅜ',
                7: 'ㅠ',
                8: 'ㅡ',
                9: 'ㅣ',
                10: 'ㅐ',
                11: 'ㅒ',
                12: 'ㅔ',
                13: 'ㅖ',
                14: 'ㅘ',
                15: 'ㅚ',
                16: 'ㅝ',
                17: 'ㅟ',
                18: 'ㅢ'
            }

            for i in range(19):
                start_y = int(h * i / 19)
                end_y = int(h * (i + 1) / 19)
                choice_img = question_img[start_y:end_y, :]
                avg_pixel_value = np.mean(choice_img)

                if avg_pixel_value < 200:
                    choices.append(hangul_jamo_map[i])
            omr_names.append(''.join(choices))
        return omr_names

    def extract_name2_3(self, img_path):   # 이름 두번째 글자의 종성
        img = self.read_img_with_cv(img_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        omr_names = []
        user_coordinates = [(266, 277, 17, 200)]

        for coordinates in user_coordinates:
            x, y, w, h = coordinates
            question_img = gray[y:y + h, x:x + w]
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            choices = []
            hangul_jamo_map = {
                0: 'ㄱ',
                1: 'ㄴ',
                2: 'ㄷ',
                3: 'ㄹ',
                4: 'ㅁ',
                5: 'ㅂ',
                6: 'ㅅ',
                7: 'ㅇ',
                8: 'ㅈ',
                9: 'ㅊ',
                10: 'ㅋ',
                11: 'ㅌ',
                12: 'ㅍ',
                13: 'ㅎ'
            }

            for i in range(14):
                start_y = int(h * i / 14)
                end_y = int(h * (i + 1) / 14)
                choice_img = question_img[start_y:end_y, :]
                avg_pixel_value = np.mean(choice_img)

                if avg_pixel_value < 210:
                    choices.append(hangul_jamo_map[i])
            omr_names.append(''.join(choices))
        return omr_names

    def extract_name2(self, img_path):   # 이름 두번째 글자
        HANGUL_START = 0xAC00

        cho_list = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']

        jung_list = ['ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ',
                     'ㅣ']

        jong_list = [''] + ['ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ',
                            'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']

        omr_names_1 = self.extract_name2_1(img_path)
        omr_names_2 = self.extract_name2_2(img_path)
        omr_names_3 = self.extract_name2_3(img_path)

        combined_names = []

        for idx, (omr_name_1, omr_name_2, omr_name_3) in enumerate(zip(omr_names_1, omr_names_2, omr_names_3)):
            try:
                if omr_name_1 not in cho_list:
                    raise ValueError(f"초성 '{omr_name_1}' at index {idx} is not valid.")
                if omr_name_2 not in jung_list:
                    raise ValueError(f"중성 '{omr_name_2}' at index {idx} is not valid.")
                if omr_name_3 and omr_name_3 not in jong_list:
                    raise ValueError(f"종성 '{omr_name_3}' at index {idx} is not valid.")

                cho_index = cho_list.index(omr_name_1)
                jung_index = jung_list.index(omr_name_2)
                jong_index = jong_list.index(omr_name_3) if omr_name_3 else 0

                code_point = (cho_index * len(jung_list) * len(jong_list)) + (
                            jung_index * len(jong_list)) + jong_index + HANGUL_START
                combined_names.append(chr(code_point))
            except ValueError as e:
                continue

        return combined_names

    def extract_name3_1(self, img_path):   # 이름 세번째 글자의 초성
        img = self.read_img_with_cv(img_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        omr_names = []
        user_coordinates = [(285, 277, 17, 200)]

        for coordinates in user_coordinates:
            x, y, w, h = coordinates
            question_img = gray[y:y + h, x:x + w]
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            choices = []
            hangul_jamo_map = {
                0: 'ㄱ',
                1: 'ㄴ',
                2: 'ㄷ',
                3: 'ㄹ',
                4: 'ㅁ',
                5: 'ㅂ',
                6: 'ㅅ',
                7: 'ㅇ',
                8: 'ㅈ',
                9: 'ㅊ',
                10: 'ㅋ',
                11: 'ㅌ',
                12: 'ㅍ',
                13: 'ㅎ'
            }

            for i in range(14):
                start_y = int(h * i / 14)
                end_y = int(h * (i + 1) / 14)
                choice_img = question_img[start_y:end_y, :]
                avg_pixel_value = np.mean(choice_img)

                if avg_pixel_value < 210:
                    choices.append(hangul_jamo_map[i])
            omr_names.append(''.join(choices))
        return omr_names

    def extract_name3_2(self, img_path):   # 이름 세번째 글자의 중성
        img = self.read_img_with_cv(img_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        omr_names = []
        user_coordinates = [(300, 277, 17, 266)]

        for coordinates in user_coordinates:
            x, y, w, h = coordinates
            question_img = gray[y:y + h, x:x + w]
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            choices = []
            hangul_jamo_map = {
                0: 'ㅏ',
                1: 'ㅑ',
                2: 'ㅓ',
                3: 'ㅕ',
                4: 'ㅗ',
                5: 'ㅛ',
                6: 'ㅜ',
                7: 'ㅠ',
                8: 'ㅡ',
                9: 'ㅣ',
                10: 'ㅐ',
                11: 'ㅒ',
                12: 'ㅔ',
                13: 'ㅖ',
                14: 'ㅘ',
                15: 'ㅚ',
                16: 'ㅝ',
                17: 'ㅟ',
                18: 'ㅢ'
            }

            for i in range(19):
                start_y = int(h * i / 19)
                end_y = int(h * (i + 1) / 19)
                choice_img = question_img[start_y:end_y, :]
                avg_pixel_value = np.mean(choice_img)

                if avg_pixel_value < 200:
                    choices.append(hangul_jamo_map[i])
            omr_names.append(''.join(choices))
        return omr_names

    def extract_name3_3(self, img_path):   # 이름 세번째 글자의 종성
        img = self.read_img_with_cv(img_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        omr_names = []
        user_coordinates = [(314, 277, 17, 200)]

        for coordinates in user_coordinates:
            x, y, w, h = coordinates
            question_img = gray[y:y + h, x:x + w]
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            choices = []
            hangul_jamo_map = {
                0: 'ㄱ',
                1: 'ㄴ',
                2: 'ㄷ',
                3: 'ㄹ',
                4: 'ㅁ',
                5: 'ㅂ',
                6: 'ㅅ',
                7: 'ㅇ',
                8: 'ㅈ',
                9: 'ㅊ',
                10: 'ㅋ',
                11: 'ㅌ',
                12: 'ㅍ',
                13: 'ㅎ'
            }

            for i in range(14):
                start_y = int(h * i / 14)
                end_y = int(h * (i + 1) / 14)
                choice_img = question_img[start_y:end_y, :]
                avg_pixel_value = np.mean(choice_img)

                if avg_pixel_value < 210:
                    choices.append(hangul_jamo_map[i])
            omr_names.append(''.join(choices))
        return omr_names

    def extract_name3(self, img_path):   # 이름 세번째 글자
        HANGUL_START = 0xAC00

        cho_list = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']

        jung_list = ['ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ',
                     'ㅣ']

        jong_list = [''] + ['ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ',
                            'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']

        omr_names_1 = self.extract_name3_1(img_path)
        omr_names_2 = self.extract_name3_2(img_path)
        omr_names_3 = self.extract_name3_3(img_path)

        combined_names = []

        for idx, (omr_name_1, omr_name_2, omr_name_3) in enumerate(zip(omr_names_1, omr_names_2, omr_names_3)):
            try:
                if omr_name_1 not in cho_list:
                    raise ValueError(f"초성 '{omr_name_1}' at index {idx} is not valid.")
                if omr_name_2 not in jung_list:
                    raise ValueError(f"중성 '{omr_name_2}' at index {idx} is not valid.")
                if omr_name_3 and omr_name_3 not in jong_list:
                    raise ValueError(f"종성 '{omr_name_3}' at index {idx} is not valid.")

                cho_index = cho_list.index(omr_name_1)
                jung_index = jung_list.index(omr_name_2)
                jong_index = jong_list.index(omr_name_3) if omr_name_3 else 0

                code_point = (cho_index * len(jung_list) * len(jong_list)) + (
                            jung_index * len(jong_list)) + jong_index + HANGUL_START
                combined_names.append(chr(code_point))
            except ValueError as e:
                continue

        return combined_names

    def extract_name(self, img_path):   # omr 이름 표에 삽입
        omr_names_1 = self.extract_name1(img_path)
        omr_names_2 = self.extract_name2(img_path)
        omr_names_3 = self.extract_name3(img_path)

        combined_names = []

        combined_names.extend([''.join(name) for name in omr_names_1])
        combined_names.extend([''.join(name) for name in omr_names_2])
        combined_names.extend([''.join(name) for name in omr_names_3])

        combined_names_str = ''.join(combined_names)

        current_row = 0

        while current_row < self.table_widget.rowCount():
            item = self.table_widget.item(current_row, 0)
            if item is None or item.text() == '':
                item = QTableWidgetItem(combined_names_str)
                self.table_widget.setItem(current_row, 0, item)
                item.setTextAlignment(Qt.AlignCenter)
                break
            current_row += 1

    def extract_number(self, img_path):   # omr 학번 표에 삽입
        img = self.read_img_with_cv(img_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        omr_numbers = []
        user_coordinates = [(99, 270, 11, 245), (113, 270, 11, 245), (127, 270, 11, 245), (142, 270, 11, 245)]

        current_row = 0
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

                if avg_pixel_value < 210:
                    choices.append(i)

            omr_numbers.append(choices)
        result = int(''.join(str(num[0]) if num else '0' for num in omr_numbers))


        while current_row < self.table_widget.rowCount():
            item = self.table_widget.item(current_row, 1)
            if item is None or item.text() == '':
                item = QTableWidgetItem(str(result))
                self.table_widget.setItem(current_row, 1, item)
                item.setTextAlignment(Qt.AlignCenter)
                break
            current_row += 1

    def extract_omr(self, img_path):   # omr 답 표에 삽입
        img = self.read_img_with_cv(img_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
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

        selected_item = self.cb.currentText()
        if selected_item:
            file_name = f"{selected_item}_table_data.json"
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
            return

        desired_coordinates_count = int(num_questions)
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

                if avg_pixel_value < 225:
                    choices.append(str(j + 1))

            omr_answers.append(choices)
        self.omr_grading(omr_answers)

        for column_idx, column_answers in enumerate(omr_answers, start=4):
            row_index = 0
            for choice in column_answers:
                current_item = self.table_widget.item(row_index, column_idx)
                if current_item is None or current_item.text() == "":
                    item = QTableWidgetItem(str(choice))
                    self.table_widget.setItem(row_index, column_idx, item)
                    item.setTextAlignment(Qt.AlignCenter)
                else:
                    while True:
                        row_index += 1
                        if row_index >= self.table_widget.rowCount():
                            break
                        if self.table_widget.item(row_index, column_idx) is None or self.table_widget.item(row_index,
                                                                                                           column_idx).text() == "":
                            break
                    if row_index < self.table_widget.rowCount():
                        item = QTableWidgetItem(str(choice))
                        self.table_widget.setItem(row_index, column_idx, item)
                        item.setTextAlignment(Qt.AlignCenter)
    
    def read_img_with_cv(self, img_path):
        img_array = np.fromfile(img_path, np.uint8)
        return cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    def load_answer(self):  # 정답과 배점 불러오기
        selected_item = self.cb.currentText()
        if selected_item:
            file_name = f"{selected_item}_table_data.json"
            if os.path.exists(file_name):
                with open(file_name, "r", encoding='utf-8') as json_file:
                    data = json.load(json_file)
                    questions = data.get("questions", [])
                    answers_scores = []
                    for question in questions:
                        if isinstance(question, dict):
                            real_answer_str = question.get("정답", "")
                            # store real answer as list type to match with multiple answers
                            # need to make a separator (normally use ,)
                            real_answer = real_answer_str.split(',')

                            '''
                            if real_answer_str:
                                real_answer = int(real_answer_str)
                            else:
                                real_answer = 0
                            '''

                            score = int(question.get("배점", 0))
                            answers_scores.append((real_answer, score))
                    return answers_scores

    def make_score(self, user_answers, answer_sheet):
        total_score = 0

        for user_answer, (correct_answer, score) in zip(user_answers, answer_sheet):
            # print(f'U: {user_answer}, C: {correct_answer}')
            # need to match between multiple user answer and multiple correct answer
            # both answers' type should be list
            assert isinstance(user_answer, list), f'user_answer type is {type(user_answer)}'
            assert isinstance(correct_answer, list), f'correct_answer type is {type(correct_answer)}'

            _user_answer = ','.join(sorted(user_answer))
            _correct_answer = ','.join(sorted(correct_answer))
            if _user_answer == _correct_answer:
                total_score += score

        return total_score

    def omr_grading(self, omr_answers):   # omr 총점 계산
        answers_scores = self.load_answer()
        total_score = self.make_score(omr_answers, answers_scores)

        row_index = 0
        while True:
            current_item = self.table_widget.item(row_index, 3)
            if current_item is None or current_item.text() == "":
                # print(f'[{row_index}] {total_score}')
                item = QTableWidgetItem(str(total_score))
                self.table_widget.setItem(row_index, 3, item)
                item.setTextAlignment(Qt.AlignCenter)
                break
            else:
                row_index += 1
                if row_index >= self.table_widget.rowCount():
                    break

    def updateTotalScore(self, item):   # 표의 항목 변경시 총점 변경
        if item.column() >= 5:
            selected_item = self.cb.currentText()
            if selected_item:
                answers_scores = self.load_answer()
                if answers_scores:
                    total_score = 0
                    row_idx = item.row()
                    answers = []
                    for column in range(4, self.table_widget.columnCount()):
                        cell_item = self.table_widget.item(row_idx, column)
                        if cell_item is not None:
                            cell_item.setTextAlignment(Qt.AlignCenter)
                            answers.append([cell_item.text()])

                    total_score = self.make_score(answers, answers_scores)
                    total_score_item = QTableWidgetItem(str(total_score))
                    self.table_widget.setItem(row_idx, 3, total_score_item)
                    total_score_item.setTextAlignment(Qt.AlignCenter)

    def addPageToStackedWidget(self, img_path):   # 다중 페이지 어플에 페이지 추가
        label = QLabel()
        pixmap = QPixmap(img_path)
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignCenter)

        self.stacked_widget.addWidget(label)

    def saveScore(self):   # 표의 값들 저장
        new_table_data = {
            "score": []
        }
        for row in range(self.table_widget.rowCount()):
            row_data = {}
            for column in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, column)
                header = self.table_widget.horizontalHeaderItem(column).text()
                row_data[header] = item.text() if item is not None else ""
            new_table_data["score"].append(row_data)

        selected_item = self.cb.currentText()
        file_name = f"{selected_item}_table_score.json"

        if os.path.exists(file_name):
            with open(file_name, "r", encoding="utf-8") as json_file:
                existing_data = json.load(json_file)
                existing_data["score"].extend(new_table_data["score"])
            table_data = existing_data
        else:
            table_data = new_table_data

        with open(file_name, "w", encoding="utf-8") as json_file:
            json.dump(table_data, json_file, ensure_ascii=False, indent=4)

    def previousPage(self):   # 다중 페이지 어플의 이전 페이지 이동
        current_index = self.stacked_widget.currentIndex()
        if current_index > 0:
            self.stacked_widget.setCurrentIndex(current_index - 1)

    def nextPage(self):   # 다중 페이지 어플의 다음 페이지 이동
        current_index = self.stacked_widget.currentIndex()
        if current_index < self.stacked_widget.count() - 1:
            self.stacked_widget.setCurrentIndex(current_index + 1)

    def showMainWidget(self):
        #TODO: circular import ?
        from omr import MainWidget
        self.exam_input_widget = MainWidget()
        self.hide()

    def showSendReportWidget(self):
        #TODO: circular import ?
        from report import SendReportWidget
        self.exam_input_widget = SendReportWidget()
        self.hide()

    def showExamInputWidget(self):
        #TODO: circular import ?
        from exam_input import ExamInputWidget
        self.exam_input_widget = ExamInputWidget()   # 새로운 화면 생성
        self.hide()   # 새로운 화면 생성