from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QAbstractItemView, QHBoxLayout, QPushButton, QPlainTextEdit, QSplitter
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont


class PageScreening(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  # Main 창 참조
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 제목
        title = QLabel('Screening')
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setFixedHeight(40)
        main_layout.addWidget(title)
        
        # ============= 좌측 50% + 우측 50% 스플리터 시작 =============
        splitter = QSplitter(Qt.Horizontal)
        
        # ===== 좌측 50%: 설계변수 + 출력변수 =====
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        # 설계 변수 정보 텍스트
        design_var_label = QLabel('확정된 설계 변수')
        design_var_font = QFont()
        design_var_font.setPointSize(12)
        design_var_font.setBold(True)
        design_var_label.setFont(design_var_font)
        design_var_label.setFixedHeight(30)
        left_layout.addWidget(design_var_label)
        
        # 테이블 생성 (4 x n: NAME, 하한값, 상한값, 단위)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['설계변수', '하한 값', '상한 값', '단위'])
        
        # 테이블 스타일 설정
        self.table.setEditTriggers(
            QAbstractItemView.DoubleClicked |
            QAbstractItemView.SelectedClicked |
            QAbstractItemView.AnyKeyPressed
        )
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #2d2d2d;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QTableWidget::item {
                padding: 5px;
                color: #e0e0e0;
                font-size: 12px;
            }
            QTableWidget QLineEdit {
                font-size: 12px;
                padding: 4px;
                background-color: #3d3d3d;
                color: #e0e0e0;
                border: 1px solid #0d47a1;
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
                font-size: 11px;
            }
        """)
        
        left_layout.addWidget(self.table, 1)
        
        # 출력 변수 레이블
        output_var_label = QLabel('확정된 출력 변수')
        output_var_font = QFont()
        output_var_font.setPointSize(12)
        output_var_font.setBold(True)
        output_var_label.setFont(output_var_font)
        output_var_label.setFixedHeight(30)
        left_layout.addWidget(output_var_label)
        
        # 출력 변수 테이블 생성 (3 x n: NAME, 목표 오차율, 생성여부)
        self.output_table = QTableWidget()
        self.output_table.setColumnCount(3)
        self.output_table.setHorizontalHeaderLabels(['출력변수', '목표 오차율', '생성여부'])
        
        # 출력 테이블 스타일 설정
        self.output_table.setEditTriggers(
            QAbstractItemView.DoubleClicked |
            QAbstractItemView.SelectedClicked |
            QAbstractItemView.AnyKeyPressed
        )
        self.output_table.setStyleSheet("""
            QTableWidget {
                background-color: #2d2d2d;
                gridline-color: #404040;
                border: 1px solid #404040;
            }
            QTableWidget::item {
                padding: 5px;
                color: #e0e0e0;
                font-size: 12px;
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
                font-size: 11px;
            }
        """)
        
        left_layout.addWidget(self.output_table, 1)
        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)
        
        # ===== 우측 50%: 모니터 창 =====
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)
        
        # 모니터링 레이블
        log_label = QLabel('실행 로그')
        log_font = QFont()
        log_font.setPointSize(12)
        log_font.setBold(True)
        log_label.setFont(log_font)
        log_label.setFixedHeight(30)
        right_layout.addWidget(log_label)
        
        # 모니터 텍스트 영역
        self.monitor_display = QPlainTextEdit()
        self.monitor_display.setReadOnly(True)
        self.monitor_display.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Courier New', monospace;
                font-size: 13px;
                padding: 5px;
                border: 1px solid #404040;
            }
        """)
        right_layout.addWidget(self.monitor_display, 1)
        right_widget.setLayout(right_layout)
        splitter.addWidget(right_widget)
        
        # 스플리터 크기 비율 설정 (5:5)
        splitter.setSizes([50, 50])
        main_layout.addWidget(splitter, 5)
        
        # ============= 좌측 50% + 우측 50% 스플리터 종료 =============
        
        # 하단: 실행 버튼
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(10, 10, 10, 10)
        
        btn_execute = QPushButton('실행')
        btn_execute.setMinimumHeight(40)
        btn_execute.setMaximumWidth(150)
        btn_execute.clicked.connect(self.on_execute)
        bottom_layout.addWidget(btn_execute)
        
        bottom_layout.addStretch()
        
        bottom_widget = QWidget()
        bottom_widget.setLayout(bottom_layout)
        main_layout.addWidget(bottom_widget, 1)
        
        self.setLayout(main_layout)
    
    def on_execute(self):
        """실행 버튼 클릭 시 호출"""
        # 실행 로직 추가 (현재는 비워둠)
        pass
    
    def refresh_table(self):
        """Main page에서 호출: DV와 OV 데이터로 테이블 업데이트"""
        # 설계 변수 테이블 업데이트
        if self.main_window.DV:
            self.table.setRowCount(len(self.main_window.DV))
            
            for i, item in enumerate(self.main_window.DV):
                # 행 높이 설정
                self.table.setRowHeight(i, 35)
                
                name = item.get('NAME', '')
                unit = item.get('UNIT', '')
                lv = item.get('LV', 0)  # 하한값
                uv = item.get('UV', 0)  # 상한값
                
                # 0열: 설계변수 (NAME)
                self.table.setItem(i, 0, QTableWidgetItem(name))
                # 1열: 하한값 (LV)
                self.table.setItem(i, 1, QTableWidgetItem(f'{lv:.3f}'))
                # 2열: 상한값 (UV)
                self.table.setItem(i, 2, QTableWidgetItem(f'{uv:.3f}'))
                # 3열: 단위 (UNIT)
                self.table.setItem(i, 3, QTableWidgetItem(unit))
        else:
            # DV가 비어있으면 테이블 초기화
            self.table.setRowCount(0)
        
        # 출력 변수 테이블 업데이트
        if self.main_window.OV:
            self.output_table.setRowCount(len(self.main_window.OV))
            
            for i, item in enumerate(self.main_window.OV):
                # 행 높이 설정
                self.output_table.setRowHeight(i, 35)
                
                name = item.get('NAME', '')
                target_error = item.get('TARGET_ERROR', '')
                
                # 0열: 출력변수 (NAME)
                self.output_table.setItem(i, 0, QTableWidgetItem(name))
                # 1열: 목표 오차율 (정수/실수를 문자열로 변환)
                self.output_table.setItem(i, 1, QTableWidgetItem(str(target_error)))
                # 2열: 생성여부 (콤보박스 - 읽기 전용으로 표시)
                label = QLabel('선택됨')
                self.output_table.setCellWidget(i, 2, label)
        else:
            # OV가 비어있으면 테이블 초기화
            self.output_table.setRowCount(0)
