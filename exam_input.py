import os
import json
from PyQt5.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QListWidget,
                             QInputDialog, QTableWidget, QLabel, QLineEdit, QTableWidgetItem, QListWidgetItem)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt

class ExamInputWidget(QWidget):   # 시험 입력 화면

    def __init__(self):
        super().__init__()
        self.initUI()
        self.loadItems()
        self.list_widget.setStyleSheet("QListWidget::item {height: 30px; font-size: 30px;}")

    def initUI(self):
        self.setWindowTitle('시험 입력 화면')
        self.setWindowIcon(QIcon('logo.jpeg'))
        self.showFullScreen()

        btn = QPushButton('메인 화면', self)
        btn1 = QPushButton('시험 입력', self)
        btn2 = QPushButton('OMR 채점', self)
        btn3 = QPushButton('성적표 인쇄', self)
        btn4 = QPushButton('추가', self)
        btn5 = QPushButton('삭제', self)
        btn.setFixedSize(120, 40)
        btn1.setFixedSize(120, 40)
        btn2.setFixedSize(120, 40)
        btn3.setFixedSize(120, 40)
        btn4.setFixedSize(85, 40)
        btn5.setFixedSize(85, 40)

        self.list_widget = QListWidget(self)   # 시험명 입력 리스트 생성
        self.list_widget.setFixedSize(180, 800)
        self.list_widget.itemClicked.connect(self.createFormsForItem)
        self.selected_text_label = QLabel(self)   # 시험명 출력
        self.selected_text_label.setGeometry(400, 150, 300, 30)

        hbox = QHBoxLayout()
        hbox.addWidget(btn4)
        hbox.addSpacing(12)
        hbox.addWidget(btn5)
        hbox.setAlignment(btn5, Qt.AlignLeft)

        vbox = QVBoxLayout()
        vbox.addWidget(btn)
        vbox.addWidget(btn1)
        vbox.addWidget(btn2)
        vbox.addWidget(btn3)
        vbox.addWidget(self.list_widget)
        vbox.addLayout(hbox)
        vbox.addStretch()

        self.setLayout(vbox)

        btn.clicked.connect(self.showMainWidget)
        btn2.clicked.connect(self.showOMRGradingWidget)
        btn3.clicked.connect(self.showSendReportWidget)
        btn4.clicked.connect(self.addItemToList)
        btn5.clicked.connect(self.removeSelectedItem)

        self.show()

    def createFormsForItem(self):   # 문제지 표 생성
        font = QFont()
        font.setPointSize(20)
        self.selected_text_label.setFont(font)

        selected_item = self.list_widget.currentItem()
        if selected_item:
            text = selected_item.text()
            self.selected_text_label.setText(f"시험명: {text}")
            file_name = f"{text}_table_data.json"

            if not os.path.exists(file_name):
                with open(file_name, "w", encoding="utf-8") as json_file:
                    json_file.write("{}")

            with open(file_name, "r", encoding="utf-8") as json_file:
                data = json.load(json_file)

                self.table_widget = QTableWidget(self)

                if isinstance(data, dict) and "questions" in data:
                    questions = data["questions"]
                    self.table_widget.setRowCount(len(questions))
                    self.table_widget.setColumnCount(len(questions[0]))
                    for row, row_data in enumerate(questions):
                        for column, (key, value) in enumerate(row_data.items()):
                            item = QTableWidgetItem(str(value))
                            item.setTextAlignment(Qt.AlignCenter)
                            self.table_widget.setItem(row, column, item)
                elif isinstance(data, list):
                    self.table_widget.setRowCount(len(data))
                    self.table_widget.setColumnCount(len(data[0]))
                    for row, row_data in enumerate(data):
                        for column, (key, value) in enumerate(row_data.items()):
                            item = QTableWidgetItem(str(value))
                            item.setTextAlignment(Qt.AlignCenter)
                            self.table_widget.setItem(row, column, item)

        if hasattr(self, 'label_before_lbl'):
            self.layout().removeWidget(self.label_before_lbl)
            self.label_before_lbl.deleteLater()

        self.label_before_lbl = QLabel('시험명: ', self)
        self.label_before_lbl.setGeometry(400, 150, 100, 30)
        self.label_before_lbl.setFont(font)
        self.label_before_lbl.show()

        if hasattr(self, 'self.selected_text_label'):
            self.layout().removeWidget(self.selected_text_label)
            self.selected_text_label.deleteLater()

        self.selected_text_label.setFont(font)
        self.selected_text_label.show()

        if hasattr(self, 'label_before_line_edit'):
            self.layout().removeWidget(self.label_before_line_edit)
            self.label_before_line_edit.deleteLater()

        self.label_before_line_edit = QLabel("문항수:", self)
        self.label_before_line_edit.setGeometry(700, 150, 100, 30)
        self.label_before_line_edit.setFont(font)
        self.label_before_line_edit.show()

        self.btn5 = QPushButton('저장', self)
        self.btn5.setFixedSize(85, 40)
        self.btn5.move(1450, 150)
        self.btn5.clicked.connect(self.saveTableData)
        self.btn5.show()

        if hasattr(self, 'line_edit'):
            self.layout().removeWidget(self.line_edit)
            self.line_edit.deleteLater()

        self.line_edit = QLineEdit(self)
        self.line_edit.setGeometry(770, 150, 50, 30)
        self.line_edit.show()
        self.line_edit.setFocus()
        self.line_edit.textChanged.connect(self.updateTableRow)

        self.updateTable()

    def updateTable(self):  # 문제지 표 업데이트
        if hasattr(self, 'table_widget'):
            self.layout().removeWidget(self.table_widget)
            self.table_widget.deleteLater()

        self.table_widget = QTableWidget(self)
        self.table_widget.setColumnCount(4)
        num_columns = int(self.line_edit.text()) if self.line_edit.text().isdigit() else 1
        if num_columns < 1:
            num_columns = 1
        self.table_widget.setRowCount(num_columns)
        self.table_widget.setHorizontalHeaderLabels(["정답", "배점", "영역", "세부내용"])
        self.table_widget.setColumnWidth(0, 150)
        self.table_widget.setColumnWidth(1, 150)
        self.table_widget.setColumnWidth(2, 400)
        self.table_widget.setColumnWidth(3, 400)
        row_height = 40
        for row in range(self.table_widget.rowCount()):
            self.table_widget.setRowHeight(row, row_height)

        # 테이블 위젯의 위치 및 크기 조정
        table_width = 1140
        table_height = 750
        table_x = 400
        table_y = 200
        self.table_widget.setGeometry(table_x, table_y, table_width, table_height)

        self.table_widget.show()
        self.loadTableData()

    def addItemToList(self):  # 시험명 입력 리스트 요소 삽입
        text, ok = QInputDialog.getText(self, '항목 추가', '항목 이름:')
        if ok and text:
            item = QListWidgetItem(text)
            item.setTextAlignment(Qt.AlignCenter)
            self.list_widget.insertItem(0, item)
            self.saveItems()

    def removeSelectedItem(self):   # 시험명 입력 리스트 요소 삭제
        list_items = self.list_widget.selectedItems()
        if not list_items: return
        for item in list_items:
            self.list_widget.takeItem(self.list_widget.row(item))
        self.saveItems()

    def saveItems(self):   # 시험명 입력 리스트의 모든 요소 저장
        items = []
        for index in range(self.list_widget.count()):
            items.append(self.list_widget.item(index).text())
        with open("list_items.txt", "w", encoding="utf-8") as file:
            file.write("\n".join(items))

    def loadItems(self):  # 시험명 입력 리스트의 모든 요소 불러오기
        if os.path.exists("list_items.txt"):
            with open("list_items.txt", "r", encoding="utf-8") as file:
                items = file.readlines()
                for item_text in items:
                    item = QListWidgetItem(item_text.strip())
                    item.setTextAlignment(Qt.AlignCenter)
                    self.list_widget.addItem(item)

    def saveTableData(self):   # 문제지 표의 내용 저장
        table_data = {
            "num_questions": self.line_edit.text(),
            "questions": []
        }
        for row in range(self.table_widget.rowCount()):
            row_data = {}
            for column in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, column)
                if item is not None:
                    row_data[self.table_widget.horizontalHeaderItem(column).text()] = item.text()
                else:
                    row_data[self.table_widget.horizontalHeaderItem(column).text()] = ""
            table_data["questions"].append(row_data)

        selected_item = self.list_widget.currentItem()
        if selected_item:
            text = selected_item.text()
            file_name = f"{text}_table_data.json"
            with open(file_name, "w", encoding="utf-8") as json_file:
                json.dump(table_data, json_file, ensure_ascii=False, indent=4)

    def loadTableData(self):   # 문제지 표의 내용 불러오기
        selected_item = self.list_widget.currentItem()
        if selected_item:
            text = selected_item.text()
            file_name = f"{text}_table_data.json"
            if os.path.exists(file_name):
                with open(file_name, "r", encoding='utf-8') as json_file:
                    data = json.load(json_file)

                    if "questions" in data:
                        num_questions = data.get("num_questions", "")
                        self.line_edit.setText(num_questions)
                        questions = data.get("questions", [])
                    elif isinstance(data, list):
                        questions = data
                        num_questions = len(questions)
                        self.line_edit.setText(str(num_questions))
                    else:
                        return

                    row_count = int(num_questions) if num_questions.isdigit() else 1
                    self.table_widget.setRowCount(row_count)

                    for row, question in enumerate(questions):
                        for column, key in enumerate(["정답", "배점", "영역", "세부내용"]):
                            value = question.get(key, "") if isinstance(question, dict) else ""
                            item = QTableWidgetItem(str(value))
                            item.setTextAlignment(Qt.AlignCenter)
                            self.table_widget.setItem(row, column, item)

    def updateTableRow(self):   # 문제지 표의 행 수 조정
        num_columns = int(self.line_edit.text()) if self.line_edit.text().isdigit() else 1
        if num_columns < 1:
            num_columns = 1
        self.table_widget.setRowCount(num_columns)

        selected_item = self.list_widget.currentItem()
        if selected_item:
            text = selected_item.text()
            file_name = f"{text}_table_data.json"
            if os.path.exists(file_name):
                with open(file_name, "r", encoding='utf-8') as json_file:
                    data = json.load(json_file)

                    if "questions" in data:
                        num_questions = num_columns
                        questions = data.get("questions", [])
                    elif isinstance(data, list):
                        questions = data
                        num_questions = num_columns
                        self.line_edit.setText(str(num_questions))
                    else:
                        return

                    row_count = num_questions if isinstance(num_questions, int) else 1
                    self.table_widget.setRowCount(row_count)

                    for row, question in enumerate(questions):
                        for column, key in enumerate(["정답", "배점", "영역", "세부내용"]):
                            value = question.get(key, "") if isinstance(question, dict) else ""
                            item = QTableWidgetItem(str(value))
                            self.table_widget.setItem(row, column, item)

    def showMainWidget(self):
        from omr import MainWidget
        self.exam_input_widget = MainWidget()
        self.hide()

    def showOMRGradingWidget(self):
        from grade import OMRGradingWidget
        self.exam_input_widget = OMRGradingWidget()
        self.hide()

    def showSendReportWidget(self):
        from report import SendReportWidget
        self.exam_input_widget = SendReportWidget()
        self.hide()
