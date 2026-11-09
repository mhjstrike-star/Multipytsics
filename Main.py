import sys
import os

# 현재 스크립트의 디렉토리를 Python 경로에 추가 (batch 파일 실행 시 import 오류 해결)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QStackedWidget, QLabel)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from page_main import PageMain
from page_screening import PageScreening
from page_AMR import PageAMR
from page_DO import PageDO

def apply_modern_stylesheet(app):
    """현대적인 다크 테마 스타일시트 적용"""
    stylesheet = """
    QMainWindow {
        background-color: #1e1e1e;
    }
    
    QWidget {
        background-color: #1e1e1e;
        color: #e0e0e0;
    }
    
    QLabel {
        color: #e0e0e0;
    }
    
    QPushButton {
        background-color: #0d47a1;
        color: #ffffff;
        border: none;
        border-radius: 5px;
        padding: 8px 16px;
        font-weight: bold;
        font-size: 12px;
    }
    
    QPushButton:hover {
        background-color: #1565c0;
    }
    
    QPushButton:pressed {
        background-color: #0d3d8f;
    }
    
    QLineEdit {
        background-color: #2d2d2d;
        color: #e0e0e0;
        border: 2px solid #0d47a1;
        border-radius: 5px;
        padding: 6px;
        font-size: 11px;
    }
    
    QLineEdit:focus {
        border: 2px solid #1976d2;
    }
    
    QComboBox {
        background-color: #2d2d2d;
        color: #e0e0e0;
        border: 2px solid #0d47a1;
        border-radius: 5px;
        padding: 6px;
    }
    
    QComboBox::drop-down {
        border: none;
    }
    
    QSpinBox, QDoubleSpinBox {
        background-color: #2d2d2d;
        color: #e0e0e0;
        border: 2px solid #0d47a1;
        border-radius: 5px;
        padding: 6px;
    }
    
    QTableWidget {
        background-color: #2d2d2d;
        gridline-color: #404040;
        border: 1px solid #404040;
    }
    
    QTableWidget::item {
        padding: 5px;
        color: #e0e0e0;
    }
    
    QTableWidget::item:selected {
        background-color: #0d47a1;
    }
    
    QHeaderView::section {
        background-color: #0d47a1;
        color: #ffffff;
        padding: 5px;
        border: none;
        font-weight: bold;
    }
    
    QCheckBox {
        color: #e0e0e0;
        spacing: 5px;
    }
    
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
    }
    
    QCheckBox::indicator:unchecked {
        background-color: #2d2d2d;
        border: 2px solid #0d47a1;
        border-radius: 3px;
    }
    
    QCheckBox::indicator:checked {
        background-color: #0d47a1;
        border: 2px solid #0d47a1;
        border-radius: 3px;
    }
    
    QSlider::groove:horizontal {
        background-color: #404040;
        height: 8px;
        margin: 2px 0;
        border-radius: 4px;
    }
    
    QSlider::handle:horizontal {
        background-color: #0d47a1;
        width: 18px;
        margin: -5px 0;
        border-radius: 9px;
    }
    
    QSlider::handle:horizontal:hover {
        background-color: #1565c0;
    }
    
    QStackedWidget {
        background-color: #1e1e1e;
    }
    """
    app.setStyleSheet(stylesheet)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pages = {}
        # 공유 변수
        self.IV_list = []  # 설계 변수 입력값 리스트
        self.DV = []       # 확정된 설계 변수 리스트
        self.OV_list = []  # 출력 변수 입력값 리스트
        self.OV = []       # 확정된 출력 변수 리스트
        self.WDIR = ""     # 작업 디렉토리
        self.SUPERCOMPUTER_PATH = ""  # 슈퍼컴 해석경로
        self.Unit=[]
        self.IP_ADDRESS = ""  # IP주소
        self.ANALYSIS_TARGET = "All"  # 해석 대상
        self.rpm4fl = ""  # rpm4fl
        self.init_ui()  
        self.ip=''    #ip 
        self.supervisor=''  #superdir     
        self.Executing = None
    def init_ui(self):
        # 창 설정
        self.setWindowTitle('Multi-Physics Software')
        
        # 초기 크기 설정
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        width = int(screen_geometry.width() * 0.8)
        height = int(screen_geometry.height() * 0.8)
        x = int((screen_geometry.width() - width) / 2)
        y = int((screen_geometry.height() - height) / 2)
        self.setGeometry(x, y, width, height)
        
        # 최소/최대 크기 설정
        self.setMinimumSize(800, 500)
        self.setMaximumSize(2000, 1200)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 좌측 네비게이션 메뉴 (고정 너비)
        self.nav_layout = QVBoxLayout()
        self.nav_layout.setSpacing(10)
        self.nav_layout.setContentsMargins(10, 10, 10, 10)
        
        nav_title = QLabel('Navigation')
        nav_title_font = QFont()
        nav_title_font.setPointSize(14)
        nav_title_font.setBold(True)
        nav_title.setFont(nav_title_font)
        self.nav_layout.addWidget(nav_title)
        
        # 구분선
        separator = QLabel()
        separator.setFixedHeight(2)
        separator.setStyleSheet("background-color: #0d47a1;")
        self.nav_layout.addWidget(separator)
        
        # 네비게이션 버튼 생성
        self.pages_list = [
            ('Main', PageMain),
            ('Screening', PageScreening),
            ('AMR', PageAMR),
            ('DO', PageDO)
        ]
        
        for page_name, page_class in self.pages_list:
            btn = QPushButton(page_name)
            btn.setMinimumHeight(50)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding-left: 15px;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 13px;
                }
                QPushButton:checked {
                    background-color: #1565c0;
                    border-left: 4px solid #64b5f6;
                }
            """)
            btn.clicked.connect(lambda checked, name=page_name: self.switch_page(name))
            self.nav_layout.addWidget(btn)
        
        self.nav_layout.addStretch()
        
        # 좌측 패널 (메뉴) - 고정 너비
        nav_widget = QWidget()
        nav_widget.setLayout(self.nav_layout)
        nav_widget.setFixedWidth(200)
        nav_widget.setStyleSheet("background-color: #1e1e1e; border-right: 1px solid #0d47a1;")
        main_layout.addWidget(nav_widget)
        
        # 우측 스택 위젯 (페이지 표시) - 확장 가능
        self.stacked_widget = QStackedWidget()
        
        # 페이지 생성 및 스택에 추가
        for page_name, page_class in self.pages_list:
            page = page_class(self)  # Main 창 참조 전달
            self.pages[page_name] = page
            self.stacked_widget.addWidget(page)
        
        main_layout.addWidget(self.stacked_widget, 1)  # 1 = 확장 비율
        
        # 첫 번째 페이지로 초기화
        self.switch_page('Main')
    
    def switch_page(self, page_name):
        """페이지 전환"""
        if page_name in self.pages:
            self.stacked_widget.setCurrentWidget(self.pages[page_name])
            
            # 모든 버튼의 체크 상태 해제 후 해당 버튼만 체크
            for page_name_btn, _ in self.pages_list:
                # 레이아웃에서 버튼 찾기
                for i in range(self.nav_layout.count()):
                    widget = self.nav_layout.itemAt(i).widget()
                    if isinstance(widget, QPushButton) and widget.text() == page_name_btn:
                        widget.setChecked(page_name_btn == page_name)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    apply_modern_stylesheet(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
