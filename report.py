import sys
import os
import json
from PyQt5.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
                             QTableWidget, QLabel, QTableWidgetItem, QComboBox, QCheckBox)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QPersistentModelIndex
from PyQt5.QtCore import Qt
import webbrowser
import math


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
class SendReportWidget(QWidget):  # 성적표 인쇄 화면

    def __init__(self):
        super().__init__()
        self.initUI()
        self.loadItems()

    def initUI(self):
        self.setWindowTitle('성적표 인쇄 화면')
        icon_path = resource_path('gr.jpg')
        self.setWindowIcon(QIcon(icon_path))
        self.showFullScreen()

        btn = QPushButton('메인 화면', self)
        btn1 = QPushButton('시험 입력', self)
        btn2 = QPushButton('OMR 채점', self)
        btn3 = QPushButton('성적표 인쇄', self)
        btn.setFixedSize(120, 40)
        btn1.setFixedSize(120, 40)
        btn2.setFixedSize(120, 40)
        btn3.setFixedSize(120, 40)

        vbox = QVBoxLayout()
        vbox.addWidget(btn)
        vbox.addWidget(btn1)
        vbox.addWidget(btn2)
        vbox.addWidget(btn3)
        vbox.addStretch()

        self.setLayout(vbox)

        btn.clicked.connect(self.showMainWidget)
        btn1.clicked.connect(self.showExamInputWidget)
        btn2.clicked.connect(self.showOMRGradingWidget)

        self.label = QLabel('시험 검색', self)
        self.label.setGeometry(190, 20, 200, 50)
        self.label.show()

        self.cb = QComboBox(self)  # 시험지 항목 콤보 박스 생성
        self.cb.setGeometry(280, 30, 160, 30)
        self.cb.show()

        self.table_widget = QTableWidget(self)
        self.table_widget.setRowCount(1)
        self.table_widget.setColumnCount(7)
        self.table_widget.setHorizontalHeaderLabels(["선택", "이름", "학번", "학급명", "학년", "핸드폰 번호", "점수"])
        self.table_widget.setGeometry(180, 150, 1500, 900)
        self.table_widget.show()

        self.btn_search = QPushButton("검색", self)
        self.btn_search.setFixedSize(120, 40)
        self.btn_search.move(1565, 20)
        self.btn_search.clicked.connect(self.updateCol)
        self.btn_search.clicked.connect(self.loadScore)
        self.btn_search.show()

        self.btn_select = QPushButton("모두 선택", self)
        self.btn_cancel = QPushButton("모두 취소", self)
        self.btn_print = QPushButton("인쇄", self)
        self.btn_select.setFixedSize(120, 40)
        self.btn_cancel.setFixedSize(120, 40)
        self.btn_print.setFixedSize(120, 40)
        self.btn_select.move(180, 100)
        self.btn_cancel.move(380, 100)
        self.btn_print.move(1180, 100)
        self.btn_select.clicked.connect(self.selectCb)
        self.btn_cancel.clicked.connect(self.cancelCb)
        self.btn_print.clicked.connect(self.printPage)

        self.btn_select.show()
        self.btn_cancel.show()
        self.btn_print.show()

        self.show()

    def loadItems(self):   # 콤보 박스의 항목 정보 불러오기
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

                    questions = data.get("questions", [])
                    areas = [question.get("영역", "") for question in questions if isinstance(question, dict)]
                    unique_areas = set(areas)
                    col_count = len(unique_areas) + 7

                    self.table_widget.setColumnCount(col_count)

                    headers = ["선택", "이름", "학번", "학급명", "학년", "핸드폰 번호", "점수"]
                    for area in unique_areas:
                        headers.append(area)
                    self.table_widget.setHorizontalHeaderLabels(headers)

    def loadScore(self):  # 채점 결과 표의 내용 불러오기
        selected_index = self.cb.currentIndex()
        if selected_index >= 0:
            selected_item = self.cb.itemText(selected_index)
            file_name = f"{selected_item}_table_score.json"
            if os.path.exists(file_name):
                with open(file_name, "r", encoding='utf-8') as json_file:
                    data = json.load(json_file)

                    questions = data.get("score", [])
                    self.adjustTable(questions)
            else:
                self.table_widget.setRowCount(1)
                self.table_widget.clearContents()

    def adjustTable(self, questions):   # 표의 행 조정 및 체크박스 추가
        row_count = len(questions)
        self.table_widget.setRowCount(row_count)

        for row, question in enumerate(questions):
            widget = QWidget()
            layout = QHBoxLayout()
            layout.addWidget(QCheckBox())
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            widget.setLayout(layout)
            self.table_widget.setCellWidget(row, 0, widget)
            for column, key in enumerate(["이름", "학번", "학급명"]):
                value = question.get(key, "") if isinstance(question, dict) else ""
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                self.table_widget.setItem(row, column + 1, item)

            if "점수" in question:
                score_value = question["점수"]
            else:
                score_value = ""
            score_item = QTableWidgetItem(str(score_value))
            score_item.setTextAlignment(Qt.AlignCenter)
            self.table_widget.setItem(row, 6, score_item)

    def selectCb(self):   # 모두 선택
        row_count = self.table_widget.rowCount()

        for row in range(row_count):
            checkbox_widget = self.table_widget.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.layout().itemAt(0).widget()
                if isinstance(checkbox, QCheckBox):
                    checkbox.setChecked(True)

    def cancelCb(self):   # 모두 취소
        row_count = self.table_widget.rowCount()

        for row in range(row_count):
            checkbox_widget = self.table_widget.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.layout().itemAt(0).widget()
                if isinstance(checkbox, QCheckBox):
                    checkbox.setChecked(False)

    def printPage(self):  # 성적표 출력
        checked_indexes = self.getCheckedIndexes()
        if checked_indexes:
            for i, index in enumerate(checked_indexes):
                file_path = f"print_page_{i}.html"
                combo_box_text = self.cb.currentText()
                table_item_text = self.table_widget.item(index.row(), 1).text()
                student_code = self.table_widget.item(index.row(), 2).data(Qt.DisplayRole)
                class_name = self.table_widget.item(index.row(), 3).data(Qt.DisplayRole)
                score_value = self.table_widget.item(index.row(), 6).data(Qt.DisplayRole)

                score_values = []
                for row in range(self.table_widget.rowCount()):
                    value = self.table_widget.item(row, 6).data(Qt.DisplayRole)
                    if value is not None:
                        score_values.append(float(value))
                avg_score = sum(score_values) / len(score_values) if score_values else 0

                file_name = f"{combo_box_text}_table_score.json"
                with open(file_name, "r", encoding="utf-8") as json_file:
                    json_data = json.load(json_file)
                    timestamp = json_data.get("timestamp", "")

                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(
                        f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <meta charset='utf-8'>
                            <title>모의고사 Report</title>
                            <style>
                                @page {{
                                    size: A4;
                                    margin: 0; /* 페이지 여백 제거 */
                                    border: 2px solid black;
                                }}
                                body {{ 
                                    font-family: Arial, sans-serif; 
                                }}
                                table {{ 
                                    width: 100%; 
                                    border-collapse: collapse; 
                                    margin: 20px 0;
                                }}
                                th, td {{ 
                                    border: 1px solid #ccc; 
                                    padding: 8px; 
                                    text-align: center; 
                                }}
                                th {{
                                    background-color: #f4f4f4; 
                                }}
                                h2 {{ 
                                    text-align: left; 
                                    margin-left: 10px;
                                    font-weight: normal;
                                     position: relative;
                                }}
                                h2::before {{
                                    content: "|";
                                    color: orange;
                                    font-weight: bold;
                                    position: absolute;
                                    left: -10px;
                                }}
                                .content {{
                                    margin-top: 20px;
                                    text-align: center;
                                }}
                                .header {{
                                    display: flex;
                                    justify-content: space-between;
                                    align-items: center;
                                    margin: 0 20px;
                                    margin-bottom: 20px;
                                    border-bottom: 2px solid #ccc;
                                }}
                            </style>
                            <script>
                                function insertExamDate() {{
                                    var today = new Date("{timestamp}");
                                    var dateString = today.getFullYear() + '-' +
                                                     ('0' + (today.getMonth() + 1)).slice(-2) + '-' +
                                                     ('0' + today.getDate()).slice(-2);
                                    document.getElementById('todayDate').innerText = dateString;
                                }}
                            </script>
                        </head>
                        <body onload="insertExamDate()">
                            <div class="header">
                                <h1>{combo_box_text}</h1>
                                <h1>주식회사 국력발전소</h1>
                            </div>

                            <h2>학생 정보</h2>
                            <table>
                                <tr>
                                    <th>성명</th>
                                    <th>학급명</th>
                                    <th>학번</th>
                                    <th>시험일</th>
                                    <th>내 점수/만점</th>
                                    <th>평균</th>
                                </tr>
                                <tr>
                                    <td>{table_item_text}</td>
                                    <td>{class_name}</td>
                                    <td>{student_code}</td>
                                    <td id="todayDate"></td>
                                    <td>{score_value} / 100</td>
                                    <td>{avg_score:.1f}</td>
                                </tr>
                            </table>

                            <h2>영역분류별 성취도 분석</h2>
                            <table>
                                <tr>
                                    <th>영역분류</th>
                                    <th>배점</th>
                                    <th>득점</th>
                                    <th>성취도%</th>
                                    <th>평균</th>
                                </tr>
                            </table>

                            <h2>문항 채점표</h2>
                            <table>
                                <tr>
                                    <th>문항</th>
                                    <th>배점</th>
                                    <th>정답</th>
                                    <th>학생답안</th>
                                    <th>정답률%</th>
                                </tr> 
                            </table>  
                        </body>
                        </html>
                    """)
                webbrowser.open("file://" + os.path.realpath(file_path))

    def getCheckedIndexes(self):
        checked_indexes = []
        row_count = self.table_widget.rowCount()
        for row in range(row_count):
            checkbox_widget = self.table_widget.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.layout().itemAt(0).widget()
                if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                    checked_indexes.append(QPersistentModelIndex(self.table_widget.model().index(row, 0)))
        return checked_indexes

    def countChecked(self):
        checked_count = 0
        row_count = self.table_widget.rowCount()
        for row in range(row_count):
            checkbox_widget = self.table_widget.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.layout().itemAt(0).widget()
                if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                    checked_count += 1
        return checked_count

    def showMainWidget(self):
        from omr import MainWidget
        self.exam_input_widget = MainWidget()
        self.hide()

    def showOMRGradingWidget(self):
        from grade import OMRGradingWidget
        self.exam_input_widget = OMRGradingWidget()
        self.hide()

    def showExamInputWidget(self):
        from exam_input import ExamInputWidget
        self.exam_input_widget = ExamInputWidget()
        self.hide()
