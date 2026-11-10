from pathlib import Path

from PySide6.QtGui                      import QFont
from PySide6.QtCore                     import Qt, QThread, Signal
from PySide6.QtWidgets                  import QApplication, QAbstractItemView, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QSpinBox, QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from functions.screening_functions      import generate_screening_design, save_screening_run_table

class ScreeningWorker(QThread):
    design_ready = Signal(dict)
    generation_failed = Signal(str)
    def __init__(self, design_variables, requested_count, sample_count, result_dir, parent):
        super().__init__(parent)
        self.design_variables = design_variables
        self.requested_count = requested_count
        self.sample_count = sample_count
        self.result_dir = result_dir

    def run(self):
        try: design = generate_screening_design(self.design_variables, self.sample_count)
        except Exception as error: self.generation_failed.emit(str(error))
        else: self.design_ready.emit(design)

class PageScreening(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  # Main 창 참조
        self.worker = None
        self.init_ui()
        QApplication.instance().aboutToQuit.connect(self.wait_for_worker)
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

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
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #2d2d2d;
                gridline-color: #404040;
                border: 1px solid #404040;}
            QTableWidget::item {
                padding: 5px;
                color: #e0e0e0;
                font-size: 12px;}
            QTableWidget QLineEdit {
                font-size: 12px;
                padding: 4px;
                background-color: #3d3d3d;
                color: #e0e0e0;
                border: 1px solid #0d47a1;}
            QTableWidget::item:selected {
                background-color: #0d47a1;}
            QHeaderView::section {
                background-color: #0d47a1;
                color: #ffffff;
                padding: 5px;
                border: none;
                font-weight: bold;
                font-size: 11px;}""")
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
        design_label = QLabel('생성된 실험표')
        design_label.setFont(design_var_font)
        right_layout.addWidget(design_label)
        self.design_table = QTableWidget()
        self.design_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.design_table.setStyleSheet(self.table.styleSheet())
        right_layout.addWidget(self.design_table, 2)

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
        
        # 하단: 실행 버튼
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(10, 10, 10, 10)
        bottom_layout.addWidget(QLabel('실험점 수'))
        self.sample_count = QSpinBox()
        self.sample_count.setRange(3, 2_147_483_647)
        self.sample_count.setValue(self.maximum_sample_count() if len(self.main_window.DV) >= 2 else 6)
        self.sample_count.setToolTip('각 설계변수는 하한·중간값·상한의 3수준을 사용합니다.')
        bottom_layout.addWidget(self.sample_count)
        self.execute_button = QPushButton('실행')
        self.execute_button.setMinimumHeight(40)
        self.execute_button.setMaximumWidth(150)
        self.execute_button.clicked.connect(self.on_execute)
        bottom_layout.addWidget(self.execute_button)
        bottom_layout.addStretch()
        bottom_widget = QWidget()
        bottom_widget.setLayout(bottom_layout)
        main_layout.addWidget(bottom_widget)
        self.setLayout(main_layout)
    
    def on_execute(self):
        if self.worker is not None:
            return

        self.design_table.setRowCount(0)
        self.design_table.setColumnCount(0)
        design_variables = [variable.copy() for variable in self.main_window.DV]
        if len(design_variables) < 2:
            self.monitor_display.setPlainText('Main에서 설계변수를 두 개 이상 확정해 주세요.')
            return

        work_dir = self.main_window.WDIR
        if not work_dir or not Path(work_dir).is_dir():
            self.monitor_display.setPlainText('Main에서 해석 폴더를 지정하고 설계변수를 확정해 주세요.')
            return

        result_dir = Path(work_dir) / 'Screening_Result'
        try:
            result_dir.mkdir(exist_ok=True)
        except OSError as error:
            self.monitor_display.setPlainText(f'Screening_Result 폴더를 만들 수 없습니다.\n{error}')
            return

        requested_count = self.sample_count.value()
        sample_count = min(requested_count, self.maximum_sample_count())
        if requested_count > sample_count:
            self.monitor_display.setPlainText(
                f'요청한 {requested_count:,}점이 생성 상한을 넘었습니다. 최대 {sample_count:,}점을 생성합니다.'
            )
        else:
            self.monitor_display.setPlainText(f'실험점 {sample_count:,}개를 생성하는 중입니다.')
        self.execute_button.setEnabled(False)
        self.sample_count.setEnabled(False)
        self.worker = ScreeningWorker(design_variables, requested_count, sample_count, result_dir, self)
        self.worker.design_ready.connect(self.show_design)
        self.worker.generation_failed.connect(self.show_generation_error)
        self.worker.finished.connect(self.finish_generation)
        self.worker.start()

    def show_design(self, design):
        result_dir = self.worker.result_dir
        if (
            self.worker.design_variables != self.main_window.DV
            or Path(self.main_window.WDIR) != result_dir.parent
        ):
            self.monitor_display.setPlainText('설계변수 또는 작업 폴더가 변경되었습니다. 새 조건으로 다시 실행해 주세요.')
            return

        output_names = [variable['NAME'] for variable in self.main_window.OV]
        headers = ['No', *design['names'], *output_names]
        pending_outputs = [''] * len(output_names)
        rows = [
            (index, *map(float, point), *pending_outputs)
            for index, point in enumerate(design['points'])
        ]
        self.design_table.setColumnCount(len(headers))
        self.design_table.setHorizontalHeaderLabels(headers)
        self.design_table.setRowCount(len(rows))
        for row, values in enumerate(rows):
            for column, value in enumerate(values):
                self.design_table.setItem(row, column, QTableWidgetItem('—' if value == '' else str(value)))
        self.design_table.resizeColumnsToContents()
        oa_counts = design['oa_counts']
        orthogonality = design['orthogonality']
        method = 'OA' if orthogonality >= 1.0 - 1e-12 else 'Near OA'
        available = ', '.join(map(str, oa_counts)) or '없음'
        requested = self.worker.requested_count
        actual = len(rows)
        messages = [
            f'{method} 실험점 {actual}개 생성 완료',
            f'요청 {requested}점 · 생성 {actual}점 · 직교성 {orthogonality:.2%}',
        ]
        if requested > self.worker.sample_count:
            messages.append(
                f'요청 점 수가 생성 상한 {self.worker.sample_count:,}점을 넘어 상한값으로 실행했습니다.'
            )
        if actual < self.worker.sample_count:
            messages.append(f'ToolBox가 요청보다 적은 {actual:,}점을 반환했습니다. 생성된 실험표를 표시합니다.')
        messages.append(f'가능한 정규 OA 실험점 수 {available}')
        try:
            saved_path = save_screening_run_table(result_dir, headers, rows)
        except OSError as error:
            messages.append(f'Runcount_Total.csv 저장 실패. 파일이 열려 있는지 확인해 주세요.\n{error}')
        else:
            messages.append(f'저장 완료 {saved_path}')
        self.monitor_display.setPlainText('\n'.join(messages))

    def show_generation_error(self, message):
        self.monitor_display.setPlainText(f'실험표 생성 실패\n{message}')

    def finish_generation(self):
        self.worker.deleteLater()
        self.worker = None
        self.execute_button.setEnabled(True)
        self.sample_count.setEnabled(True)

    def wait_for_worker(self):
        if self.worker is not None:
            self.worker.wait()

    def maximum_sample_count(self):
        # Each confirmed variable has three levels. Keep the preview at most 1,000 rows.
        return min(1000, 3 ** len(self.main_window.DV))

    def refresh_table(self):
        self.design_table.setRowCount(0)
        self.design_table.setColumnCount(0)
        self.monitor_display.clear()
        if len(self.main_window.DV) >= 2:
            self.sample_count.setValue(self.maximum_sample_count())
        if self.main_window.DV: # 설계 변수 테이블 업데이트
            self.table.setRowCount(len(self.main_window.DV))
            for i, item in enumerate(self.main_window.DV):
                self.table.setRowHeight(i, 35)
                name = item.get('NAME', '')
                unit = item.get('UNIT', '')
                lv = item.get('LV', 0)  # 하한값
                uv = item.get('UV', 0)  # 상한값
                self.table.setItem(i, 0, QTableWidgetItem(name)) # 0열: 설계변수 (NAME)
                self.table.setItem(i, 1, QTableWidgetItem(str(lv))) # 1열: 하한값 (LV)
                self.table.setItem(i, 2, QTableWidgetItem(str(uv))) # 2열: 상한값 (UV)
                self.table.setItem(i, 3, QTableWidgetItem(unit)) # 3열: 단위 (UNIT)
        else:
            self.table.setRowCount(0) # DV가 비어있으면 테이블 초기화
        
        # 출력 변수 테이블 업데이트
        if self.main_window.OV:
            self.output_table.setRowCount(len(self.main_window.OV))
            for i, item in enumerate(self.main_window.OV):
                self.output_table.setRowHeight(i, 35)
                name = item.get('NAME', '')
                target_error = item.get('TARGET_ERROR', '')
                self.output_table.setItem(i, 0, QTableWidgetItem(name)) # 0열: 출력변수 (NAME)
                self.output_table.setItem(i, 1, QTableWidgetItem(str(target_error))) # 1열: 목표 오차율 (정수/실수를 문자열로 변환), 2열: 생성여부 (콤보박스 - 읽기 전용으로 표시)
                label = QLabel('선택됨')
                self.output_table.setCellWidget(i, 2, label)
        else:
            self.output_table.setRowCount(0) # OV가 비어있으면 테이블 초기화