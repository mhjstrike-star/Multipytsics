import os
import math
import traceback
import multiprocessing as mp
import functions.amr_functions as amr  # AMR 관련 함수 모듈 임포트

from PySide6.QtGui                  import QFont
from PySide6.QtCore                 import Qt, QTimer, QThread, Signal
from PySide6.QtWidgets              import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QAbstractItemView, QHBoxLayout, QDoubleSpinBox, QPushButton, QAbstractSpinBox, QPlainTextEdit, QSplitter, QLineEdit, QFileDialog, QScrollArea

class AMRWorker(mp.Process):
    def __init__(self, nx, nobj, ncon, xl, xu, size_limit, accuracy_limit, cpath, opath, rpm4fl, ip, xname, yname, Unit, what,restart=False, ppath=None):
        super().__init__()
        self.nx = nx
        self.nobj = nobj
        self.ncon = ncon
        self.xl = xl
        self.xu = xu
        self.size_limit = size_limit
        self.accuracy_limit = accuracy_limit
        self.cpath = cpath
        self.opath = opath
        self.rpm4fl = rpm4fl
        self.ip = ip
        self.xname = xname
        self.yname = yname
        self.Unit = Unit
        self.what = what
        self.restart = restart
        self.ppath = ppath
        self._task = None
    
    def run(self):
        try:
            amr.main(
                nx=self.nx, nobj=self.nobj, ncon=self.ncon,
                xl=self.xl, xu=self.xu,
                size_limit=self.size_limit,
                accuracy_limit=self.accuracy_limit,
                cpath=self.cpath,
                opath=self.opath,
                rpm4fl=self.rpm4fl,
                ip=self.ip,
                xname=self.xname,
                yname=self.yname,
                Unit=self.Unit,
                what=self.what,
                restart=self.restart,
                ppath=self.ppath
            )

        except Exception:
            with open(os.path.join(self.opath, 'amrfunction.log'), 'a', encoding='utf-8') as log:
                traceback.print_exc(file=log)
            raise

    def stop(self):
        if self.is_alive():
            self.terminate()

class PageAMR(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  # Main 창 참조
        self.log_file_path = None  # 모니터링할 로그 파일 경로
        self.log_position = 0  # 마지막으로 읽은 파일 위치
        self.log_timer = QTimer()  # 로그 파일 감시 타이머
        self.log_timer.timeout.connect(self.poll_worker)  # 타이머 연결
        self.init_ui()
        self.amr_worker = None
        self.stop_requested = False

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        title = QLabel('AMR')
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
        self.output_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked | QAbstractItemView.AnyKeyPressed)
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
            }""")
        left_layout.addWidget(self.output_table, 1)
        
        # 파라미터 입력 섹션
        params_label = QLabel('파라미터')
        params_font = QFont()
        params_font.setPointSize(11)
        params_font.setBold(True)
        params_label.setFont(params_font)
        params_label.setFixedHeight(25)
        left_layout.addWidget(params_label)
        
        # 파라미터 입력 레이아웃 (가로)
        params_layout = QHBoxLayout()
        params_layout.setSpacing(10)
        
        # 최대 실험점 개수
        max_exp_label = QLabel('최대 실험점 개수:')
        max_exp_label.setMinimumWidth(120)
        self.max_exp_spinbox = QDoubleSpinBox()
        self.max_exp_spinbox.setMinimum(1)
        self.max_exp_spinbox.setMaximum(10000)
        self.max_exp_spinbox.setValue(100)
        self.max_exp_spinbox.setDecimals(0)
        self.max_exp_spinbox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.max_exp_spinbox.setMinimumHeight(30)
        self.max_exp_spinbox.setMinimumWidth(80)
        params_layout.addWidget(max_exp_label)
        params_layout.addWidget(self.max_exp_spinbox)
        
        # 수렴 종료 조건
        convergence_label = QLabel('수렴 종료:')
        convergence_label.setMinimumWidth(70)
        self.convergence_spinbox = QDoubleSpinBox()
        self.convergence_spinbox.setMinimum(1)
        self.convergence_spinbox.setMaximum(1000)
        self.convergence_spinbox.setValue(10)
        self.convergence_spinbox.setDecimals(0)
        self.convergence_spinbox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.convergence_spinbox.setMinimumHeight(30)
        self.convergence_spinbox.setMinimumWidth(80)
        params_layout.addWidget(convergence_label)
        params_layout.addWidget(self.convergence_spinbox)
        params_layout.addStretch()
        
        left_layout.addLayout(params_layout)
        
        # 실행 및 중단 버튼 (같은 라인)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        btn_execute = QPushButton('실행')
        btn_execute.setMinimumHeight(35)
        btn_execute.setMaximumWidth(150)
        btn_execute.clicked.connect(self.on_execute)
        button_layout.addWidget(btn_execute)
        
        btn_stop = QPushButton('중단')
        btn_stop.setMinimumHeight(35)
        btn_stop.setMaximumWidth(150)
        btn_stop.clicked.connect(self.stop_running)
        button_layout.addWidget(btn_stop)
        
        button_layout.addStretch()
        
        left_layout.addLayout(button_layout)

        
        # 작업 이어하기 섹션
        continue_work_label = QLabel('작업 이어하기')
        continue_work_font = QFont()
        continue_work_font.setPointSize(10)
        continue_work_font.setBold(True)
        continue_work_label.setFont(continue_work_font)
        continue_work_label.setFixedHeight(25)
        left_layout.addWidget(continue_work_label)
        
        # 작업 이어하기 입력 레이아웃
        continue_layout = QHBoxLayout()
        continue_layout.setSpacing(5)
        
        info_path_label = QLabel('파일:')
        info_path_label.setMinimumWidth(40)
        self.info_path = QLineEdit()
        self.info_path.setPlaceholderText('분석 결과 파일 선택')
        self.info_path.setMinimumHeight(30)
        
        btn_browse = QPushButton('탐색')
        btn_browse.setMinimumHeight(30)
        btn_browse.setMaximumWidth(80)
        btn_browse.clicked.connect(self.on_browse_file)
        
        btn_execute2 = QPushButton('실행')
        btn_execute2.setMinimumHeight(30)
        btn_execute2.setMaximumWidth(80)
        btn_execute2.clicked.connect(self.on_execute2)
        
        continue_layout.addWidget(info_path_label)
        continue_layout.addWidget(self.info_path)
        continue_layout.addWidget(btn_browse)
        continue_layout.addWidget(btn_execute2)
        
        left_layout.addLayout(continue_layout)
        left_layout.addStretch()
        
        left_widget.setLayout(left_layout)
        left_widget.setMinimumWidth(0)  # 최소 너비 제거로 스플리터 비율 조절 가능
        
        # 좌측을 스크롤 가능하게 만들기
        scroll_area = QScrollArea()
        scroll_area.setWidget(left_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumWidth(0)  # 최소 너비 제거
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #1e1e1e;
                border: none;
            }""")
        splitter.addWidget(scroll_area)
        
        # ===== 우측 50%: 로그 모니터링 =====
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)
        
        # 로그 모니터링 레이블
        log_label = QLabel('실행 로그')
        log_font = QFont()
        log_font.setPointSize(12)
        log_font.setBold(True)
        log_label.setFont(log_font)
        log_label.setFixedHeight(30)
        right_layout.addWidget(log_label)
        
        # 로그 텍스트 영역
        self.log_display = QPlainTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Courier New', monospace;
                font-size: 13px;
                padding: 5px;
                border: 1px solid #404040;
            }""")
        right_layout.addWidget(self.log_display, 1)
        right_widget.setLayout(right_layout)
        splitter.addWidget(right_widget)
        
        # 스플리터 설정
        splitter.setCollapsible(0, False)  # 좌측 접기 불가
        splitter.setCollapsible(1, False)  # 우측 접기 불가
        splitter.setSizes([65, 35])  # 비율 설정
        main_layout.addWidget(splitter, 1)
        
        self.setLayout(main_layout)
        
    def stop_running(self):
        worker = self.amr_worker
        if worker is not None and worker.is_alive() and not self.stop_requested:
            worker.stop()
            self.stop_requested = True
            self.log_display.appendPlainText("작업 중단 요청")

    def can_start(self):
        if self.amr_worker is not None:
            if self.amr_worker.is_alive():
                self.log_display.appendPlainText("이미 실행 중입니다.")
                return False
            self.poll_worker()
        return True

    def start_worker(self, worker):
        worker.start()
        self.amr_worker = worker
        self.stop_requested = False
        self.main_window.Executing = True
        self.log_display.appendPlainText("작업 이어하기 시작" if worker.restart else "작업 실행")
        self.log_timer.start(1000)

    def poll_worker(self):
        worker = self.amr_worker
        if worker is None:
            return
        exit_code = worker.exitcode
        self.update_log()
        if exit_code is None:
            return

        worker.join()
        worker.close()
        self.amr_worker = None
        self.main_window.Executing = None
        self.log_timer.stop()
        if self.stop_requested:
            message = "작업 중단 완료."
        elif exit_code == 0:
            message = "실행 완료"
        else:
            message = f"실행 실패 (종료 코드 {exit_code})"
        self.log_display.appendPlainText(message)

    def on_execute(self):
        self.start_run()

    def on_browse_file(self): # 파일 탐색 버튼 클릭 시 호출
        file_path, _ = QFileDialog.getOpenFileName(self, '분석 결과 파일 선택', self.main_window.WDIR, 'CSV Files (*.csv);;All Files (*)')
        if file_path: self.info_path.setText(file_path)

    def on_execute2(self): # 이어하기 실행 버튼 클릭 시 호출
        self.start_run(restart=True)

    def start_run(self, restart=False):
        if not self.can_start():
            return

        try:
            settings = self.run_settings(restart)
            work_dir = settings['opath']
            result_dir = settings['cpath']
            old_files = ['AMR.LOG', 'convergence_info.bin'] if restart else ['AMR.LOG']
            for filename in old_files:
                path = os.path.join(result_dir, filename)
                if os.path.isfile(path):
                    os.remove(path)

            if restart:
                self.prepare_restart(work_dir)
            else:
                amr.AMR_setting(work_dir)

            self.log_file_path = os.path.join(work_dir, 'amrfunction.log')
            self.log_position = 0
            self.log_display.clear()
            self.start_worker(AMRWorker(**settings))
        except Exception as error:
            self.log_display.appendPlainText(f"AMR 실행 오류: {error}")

    def run_settings(self, restart):
        work_dir = self.main_window.WDIR
        if not work_dir or not os.path.isdir(os.path.join(work_dir, 'base')):
            raise ValueError("Main에서 해석 결과 폴더를 지정하고 설계변수를 확정해 주세요.")
        if not self.table.rowCount() or not self.output_table.rowCount():
            raise ValueError("설계변수와 출력변수를 각각 하나 이상 확정해 주세요.")

        xname, xl, xu, units = [], [], [], []
        for row in range(self.table.rowCount()):
            name = self.cell_text(self.table, row, 0)
            try:
                lower = float(self.cell_text(self.table, row, 1))
                upper = float(self.cell_text(self.table, row, 2))
            except ValueError:
                raise ValueError(f"설계변수 {row + 1}행의 하한·상한에 숫자를 입력해 주세요.") from None
            if not name or not (math.isfinite(lower) and math.isfinite(upper) and lower < upper):
                raise ValueError(f"설계변수 {row + 1}행의 이름과 범위를 확인해 주세요. 하한은 상한보다 작아야 합니다.")
            xname.append(name)
            xl.append(lower)
            xu.append(upper)
            units.append(self.cell_text(self.table, row, 3))

        yname, accuracy_limit = [], []
        for row in range(self.output_table.rowCount()):
            name = self.cell_text(self.output_table, row, 0)
            try:
                error = float(self.cell_text(self.output_table, row, 1))
            except ValueError:
                raise ValueError(f"출력변수 {row + 1}행의 목표 오차율에 숫자를 입력해 주세요.") from None
            if not name or not math.isfinite(error) or error < 0:
                raise ValueError(f"출력변수 {row + 1}행의 이름과 목표 오차율을 확인해 주세요.")
            yname.append(name)
            accuracy_limit.append(error * 0.01)

        ips = self.main_window.IP_ADDRESS
        if not ips or any(not ip.strip() for ip in ips):
            raise ValueError("Main에서 사용할 노드의 서버 IP를 입력해 주세요.")
        try:
            rpm = float(self.main_window.rpm4fl)
        except ValueError:
            raise ValueError("Main의 rpm4fl에 숫자를 입력해 주세요.") from None
        if not math.isfinite(rpm):
            raise ValueError("Main의 rpm4fl에 유한한 숫자를 입력해 주세요.")

        info_path = self.info_path.text().strip() if restart else None
        if restart:
            if not os.path.isfile(info_path):
                raise ValueError("이어하기에 사용할 CSV 파일을 선택해 주세요.")
            amr.load_restart_points(info_path, len(xname) + len(yname))

        if not callable(getattr(amr.run_analysis, 'AutoCal', None)):
            raise ValueError("고객사 해석 모듈 functions/run_analysis.py에 AutoCal을 연결해 주세요.")

        return dict(
            nx=len(xname), nobj=1, ncon=len(yname) - 1, xl=xl, xu=xu,
            size_limit=int(self.max_exp_spinbox.value()), accuracy_limit=accuracy_limit,
            cpath=os.path.join(work_dir, 'AMR_Result'), opath=work_dir,
            rpm4fl=rpm, ip=ips, xname=xname, yname=yname, Unit=units,
            what=self.main_window.ANALYSIS_TARGET, restart=restart, ppath=info_path,
        )

    @staticmethod
    def cell_text(table, row, column):
        item = table.item(row, column)
        return item.text().strip() if item is not None else ""

    def prepare_restart(self, work_dir):
        count_file = os.path.join(work_dir, 'runcount.txt')
        wdir_path = os.path.join(work_dir, 'wdir')
        if os.path.exists(wdir_path):
            folders = [d for d in os.listdir(wdir_path) if os.path.isdir(os.path.join(wdir_path, d)) and d.isdigit()]
            max_folder_num = max((int(folder) for folder in folders), default=0)
        else:
            max_folder_num = 0

        with open(count_file, 'w') as f:
            f.write(str(max_folder_num))

    def update_log(self):
        if not self.log_file_path or not os.path.exists(self.log_file_path):
            return
        
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                # 마지막으로 읽은 위치에서 시작
                f.seek(self.log_position)
                new_content = f.read()
                
                if new_content:
                    self.log_display.appendPlainText(new_content.rstrip())
                    self.log_position = f.tell()
                    self.log_display.verticalScrollBar().setValue(self.log_display.verticalScrollBar().maximum())
        except Exception as e:
            print(f"로그 파일 읽기 오류: {e}")
    
    def refresh_table(self):
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
