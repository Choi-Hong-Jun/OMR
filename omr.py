import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, QLabel)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt

from exam_input import ExamInputWidget
from grade import OMRGradingWidget
from report import SendReportWidget


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
class MainWidget(QWidget):   # 메인 화면

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('OMR 스캐너')   # 화면 제목 적용
        icon_path = resource_path('gr.jpg')  # 리소스 경로 설정
        self.setWindowIcon(QIcon(icon_path))   # 국력발전소 로고 적용
        self.showFullScreen()   # 전체 화면으로 설정

        btn = QPushButton('메인 화면', self)   # 버튼 생성
        btn1 = QPushButton('시험 입력', self)
        btn2 = QPushButton('OMR 채점', self)
        btn3 = QPushButton('성적표 인쇄', self)
        btn.setFixedSize(120, 40)   # 버튼의 크기 설정
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

        self.notice_label = QLabel("유의 사항\n\n\n   1. 복수정답시 콤마 용 예) 1,2\n\n   2. omr 결과 꼭 대조\n\n   3. omr 용지가 모두 올바른 방향으로 스캔되어야 사용 가능", self)
        self.notice_label.setFont(QFont('Arial', 40))
        self.notice_label.setAlignment(Qt.AlignCenter)
        self.notice_label.setWordWrap(True)
        self.notice_label.setStyleSheet(
            "QLabel {"
            "border: 1px solid black;"
            "border-radius: 10px;"
            "padding: 10px;" 
            "background-color: #ffffff;"
            "}"
        )
        self.notice_label.setFixedSize(1200, 800)
        self.notice_label.move(300, 200)
        self.notice_label.show()

        btn1.clicked.connect(self.showExamInputWidget)   # 시험 입력 버튼과 함수 연결
        btn2.clicked.connect(self.showOMRGradingWidget)   # OMR 채점 버튼과 함수 연결
        btn3.clicked.connect(self.showSendReportWidget)   # 성적표 인쇄 버튼과 함수 연결

        self.show()

    def showExamInputWidget(self):
        self.exam_input_widget = ExamInputWidget()   # 새로운 화면 생성
        self.hide()

    def showOMRGradingWidget(self):
        self.exam_input_widget = OMRGradingWidget()
        self.hide()

    def showSendReportWidget(self):
        self.exam_input_widget = SendReportWidget()
        self.hide()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWidget()
    sys.exit(app.exec_())
