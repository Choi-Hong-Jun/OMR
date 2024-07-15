import sys
import os
import json
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QFileDialog, QTableWidget,
                             QLabel, QLineEdit, QTableWidgetItem, QComboBox, QStackedWidget)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt
from datetime import datetime
from read_omr import OMRReader


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class OMRGradingWidget(QWidget):  # OMR 채점 화면

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

        self.cb = QComboBox(self)  # 시험지 항목 콤보 박스 생성
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

        self.stacked_widget = QStackedWidget(self)  # pdf 파일 출력 다중 페이지 어플 생성
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

    def loadItems(self):  # 콤보 박스의 항목 정보 불러오기
        self.cb.addItem("")
        if os.path.exists("list_items.txt"):
            with open("list_items.txt", "r", encoding="utf-8") as file:
                items = file.readlines()
                self.cb.addItems(item.strip() for item in items)

    def updateCol(self):  # 표의 열 수 조정
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

        for row_index in range(row_count):  # 학급명 표에 입력
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
            self._ans = _ans
            self.update_answer(_ans)

        if nr_pages > 1:
            self.btn_prevpage.show()
            self.btn_nextpage.show()
        else:
            self.btn_prevpage.hide()
            self.btn_nextpage.hide()

    def update_name(self, one_name):
        for row_index in range(self.table_widget.rowCount()):
            item = self.table_widget.item(row_index, 0)
            if not item or not item.text():
                item = QTableWidgetItem(one_name)
                self.table_widget.setItem(row_index, 0, item)
                item.setTextAlignment(Qt.AlignCenter)
                break

    def update_number(self, num):
        current_row = 0
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

    def load_answer(self):  # 정답과 배점과 영역 불러오기
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
                            real_answer = real_answer_str.split(',')
                            score = int(question.get("배점", 0))
                            section = question.get("영역", "")
                            answers_scores.append((real_answer, score, section))
                    return answers_scores

    def make_score(self, user_answers, answer_sheet):   # 점수 계산
        total_score = 0

        for user_answer, (correct_answer, score, section) in zip(user_answers, answer_sheet):
            assert isinstance(user_answer, list), f'user_answer type is {type(user_answer)}'
            assert isinstance(correct_answer, list), f'correct_answer type is {type(correct_answer)}'

            _user_answer = ','.join(sorted(user_answer))
            _correct_answer = ','.join(sorted(correct_answer))
            if _user_answer == _correct_answer:
                total_score += score

        return total_score

    def make_section_scores(self, user_answers_list, answer_sheet):
        section_scores = {}

        # Initialize section_scores based on answer_sheet sections
        for _, (_, _, section) in enumerate(answer_sheet):
            section_scores[section] = 0

        students_section_scores = []

        for user_answers in user_answers_list:
            current_student_scores = section_scores.copy()

            for user_answer, (correct_answer, score, section) in zip(user_answers, answer_sheet):
                assert isinstance(user_answer, list), f'user_answer type is {type(user_answer)}'
                assert isinstance(correct_answer, list), f'correct_answer type is {type(correct_answer)}'

                _user_answer = ','.join(sorted(user_answer))
                _correct_answer = ','.join(sorted(correct_answer))
                if _user_answer == _correct_answer:
                    current_student_scores[section] += score

            students_section_scores.append(current_student_scores)

        return students_section_scores

    def omr_grading(self, omr_answers):  # omr 총점 계산
        answers_scores = self.load_answer()
        total_score = self.make_score(omr_answers, answers_scores)

        row_index = 0
        while True:
            current_item = self.table_widget.item(row_index, 3)
            if current_item is None or current_item.text() == "":
                item = QTableWidgetItem(str(total_score))
                self.table_widget.setItem(row_index, 3, item)
                item.setTextAlignment(Qt.AlignCenter)
                break
            else:
                row_index += 1
                if row_index >= self.table_widget.rowCount():
                    break

    def updateTotalScore(self, item):  # 표의 항목 변경시 총점 변경
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

    def addPageToStackedWidget(self, img_path):  # 다중 페이지 어플에 페이지 추가
        label = QLabel()
        pixmap = QPixmap(img_path)
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignCenter)

        self.stacked_widget.addWidget(label)

    def saveScore(self):
        new_table_data = {
            "score": [],
        }

        # Collect data from table widget
        for row in range(self.table_widget.rowCount()):
            row_data = {"timestamp": datetime.now().isoformat()}
            for column in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, column)
                if item is not None:
                    header = self.table_widget.horizontalHeaderItem(column).text()
                    row_data[header] = item.text()
            new_table_data["score"].append(row_data)

        # Convert user answers to a list of lists
        user_answers_list = []
        for row_data in new_table_data["score"]:
            answers = []
            for i in range(4, self.table_widget.columnCount()):
                header = self.table_widget.horizontalHeaderItem(i).text()
                if header in row_data:
                    answers.append(row_data[header].split(','))  # Assuming answers are comma-separated
                else:
                    answers.append([])  # Handle missing data as needed
            user_answers_list.append(answers)

        # Load answer sheet
        answer_sheet = self.load_answer()

        # Calculate section scores
        section_scores = self.make_section_scores(user_answers_list, answer_sheet)

        # Update section scores in new_table_data
        for i, row_data in enumerate(new_table_data["score"]):
            for section, score in section_scores[i].items():
                row_data[section] = score

        # Save updated table data to JSON file
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

    def previousPage(self):  # 다중 페이지 어플의 이전 페이지 이동
        current_index = self.stacked_widget.currentIndex()
        if current_index > 0:
            self.stacked_widget.setCurrentIndex(current_index - 1)

    def nextPage(self):  # 다중 페이지 어플의 다음 페이지 이동
        current_index = self.stacked_widget.currentIndex()
        if current_index < self.stacked_widget.count() - 1:
            self.stacked_widget.setCurrentIndex(current_index + 1)

    def showMainWidget(self):
        from omr import MainWidget
        self.exam_input_widget = MainWidget()     # 새로운 화면 생성
        self.hide()

    def showSendReportWidget(self):
        from report import SendReportWidget
        self.exam_input_widget = SendReportWidget()
        self.hide()

    def showExamInputWidget(self):
        from exam_input import ExamInputWidget
        self.exam_input_widget = ExamInputWidget()
        self.hide()
