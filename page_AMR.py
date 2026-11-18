import re
import os
import math
import asyncio
import multiprocessing                  as mp   
import functions.amr_functions          as amr  # AMR 관련 함수 모듈 임포트
from pathlib                            import Path
from PySide6.QtGui                      import QFont
from PySide6.QtCore                     import Qt, QTimer, QThread, Signal, QSignalBlocker
from PySide6.QtWidgets                  import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QAbstractItemView, QHBoxLayout, QDoubleSpinBox, QPushButton, QAbstractSpinBox, QPlainTextEdit, QSplitter, QLineEdit, QFileDialog, QScrollArea, QComboBox, QHeaderView, QSizePolicy

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
        self._task = None  # ⭐ 초기화 추가
    
    def run(self):
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

class AMRConvergenceChart(QWidget):
    TARGET_PREFIX = 'Target value for Normalized RMSE of'
    TARGET_ROW = re.compile(r'(.+?)\s*,\s*(\S+)')
    ITERATION_ROW = re.compile(r'iteration:\s*(\d+)\b', re.IGNORECASE)
    def __init__(self, parent=None):
        super().__init__(parent)
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
        from matplotlib.figure import Figure
        from matplotlib.ticker import MaxNLocator
        self.log_path = None
        self.output_names = ()
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.refresh)
        self.output_selector = QComboBox()
        self.output_selector.setAccessibleName('출력 변수')
        self.output_selector.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.output_selector.setMinimumContentsLength(4)
        self.output_selector.currentIndexChanged.connect(self.draw_chart)
        header = QHBoxLayout()
        title = QLabel('수렴 이력')
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setFixedHeight(30)
        header.addWidget(title, 1)
        header.addWidget(self.output_selector)
        figure = Figure(facecolor='#1e1e1e', layout='constrained')
        self.canvas = FigureCanvasQTAgg(figure)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        self.axes = figure.add_subplot()
        self.iteration_locator = MaxNLocator
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addLayout(header)
        layout.addWidget(self.canvas, 1)
        self.reset_history()

    def reset_history(self):
        self.position = 0
        self.file_id = None
        self.targets = {}
        self.history = {}
        self.iteration = None
        self.column_header = ''
        self.reading_targets = False
        self.target_rows = []
        self.final_summary = False
        with QSignalBlocker(self.output_selector):
            self.output_selector.clear()
            self.output_selector.setEnabled(False)
        self.draw_chart()

    def follow_log(self, path, output_names):
        self.timer.stop()
        self.log_path = path
        self.output_names = tuple(output_names)
        self.reset_history()
        self.timer.start()

    def finish(self):
        self.timer.stop()
        self.refresh(final=True)

    def refresh(self, final=False):
        if self.log_path is None:
            return
        try:
            with self.log_path.open('rb') as log:
                stat = os.fstat(log.fileno())
                file_id = (stat.st_dev, stat.st_ino)
                if self.file_id is not None and (self.file_id != file_id or stat.st_size < self.position):
                    self.reset_history()
                self.file_id = file_id
                if stat.st_size <= self.position or self.final_summary:
                    return
                log.seek(self.position)
                changed = False
                # Read only data present when this poll started.
                data = log.read(stat.st_size - self.position)
                if not final:
                    data = data[:data.rfind(b'\n') + 1]
                for line in data.splitlines():
                    changed |= self.parse_line(line.decode('utf-8', errors='replace').strip())
                    if self.final_summary:
                        break
                self.position += len(data)
        except OSError: # The engine may not have created the file yet or may hold a write lock.
            return

        if changed:
            names = dict.fromkeys((*self.targets, *self.history))
            with QSignalBlocker(self.output_selector):
                for name in names:
                    if self.output_selector.findText(name) == -1:
                        self.output_selector.addItem(name)
                        index = self.output_selector.count() - 1
                        self.output_selector.setItemData(index, name, Qt.ItemDataRole.ToolTipRole)
                self.output_selector.setEnabled(self.output_selector.count() > 0)
            self.draw_chart()

    def display_names(self, log_names):
        # The engine writes results in the same order as its fname argument.
        if len(log_names) == len(self.output_names):
            return self.output_names
        return log_names

    def parse_line(self, line):
        if line.startswith(self.TARGET_PREFIX):
            self.reading_targets = True
            self.target_rows = []
            line = line[len(self.TARGET_PREFIX):].strip()
        changed = False
        if self.reading_targets:
            target = self.TARGET_ROW.fullmatch(line)
            if target:
                name, value = target.groups()
                self.target_rows.append((name.strip(), self.error_percent(value)))
                return False

            self.reading_targets = False
            names = self.display_names([name for name, _ in self.target_rows])
            targets = {name: percent for name, (_, percent) in zip(names, self.target_rows) if percent is not None}
            changed = targets != self.targets
            self.targets = targets
        if line.startswith('Results of Final Metamodels'):
            self.final_summary = True
            return changed
        step = self.ITERATION_ROW.match(line)
        if step:
            self.iteration = int(step[1]) + 1
            self.column_header = ''
        elif self.iteration is not None and line.startswith('convergence_info'):
            self.column_header = line.removeprefix('convergence_info').strip()
        elif self.column_header and line.startswith('best accuracy'):
            values = line.split()[2:]
            log_names = re.split(r'\s{2,}|\t+', self.column_header)
            if len(log_names) != len(values):
                log_names = self.column_header.split()
            self.column_header = ''
            if len(log_names) == len(values):
                for name, value in zip(self.display_names(log_names), values):
                    percent = self.error_percent(value)
                    if percent is not None:
                        points = self.history.setdefault(name, {})
                        if points.get(self.iteration) != percent:
                            points[self.iteration] = percent
                            changed = True
        return changed

    @staticmethod
    def error_percent(value):
        try:
            percent = float(value) * 100
        except ValueError:
            return None
        return percent if math.isfinite(percent) and percent >= 0 else None

    def draw_chart(self):
        axes = self.axes
        axes.clear()
        axes.set_facecolor('#1b1c34')
        axes.tick_params(colors='#e0e0e0', labelsize=9)
        for spine in axes.spines.values():
            spine.set_color('#555671')
        axes.set_xlabel('Iteration', color='#e0e0e0')
        axes.set_ylabel('Error (%)', color='#e0e0e0')
        name = self.output_selector.currentText()
        self.output_selector.setToolTip(name)
        points = sorted(self.history.get(name, {}).items())
        if points:
            iterations, errors = zip(*points)
            target = self.targets.get(name)
            if target is not None:
                axes.plot(iterations, [target] * len(iterations), color='#ff9094', marker='o', markersize=4, label='Target Error')
            axes.plot(iterations, errors, color='#22e1ee', marker='s', markersize=4, label='Current Error')
            for iteration, error in points:
                axes.annotate(
                    f'{error:.3g}', (iteration, error),
                    xytext=(0, 7), textcoords='offset points', ha='center',
                    color='#e0e0e0', fontsize=9,
                )
            axes.margins(x=0.07, y=0.22)
            axes.xaxis.set_major_locator(self.iteration_locator(integer=True, min_n_ticks=1))
            axes.grid(axis='y', color='#555671', alpha=0.35)
            axes.legend(
                loc='lower center', bbox_to_anchor=(0.5, 1), ncol=2,
                frameon=False, labelcolor='#e0e0e0', fontsize=8,
                columnspacing=0.5, handletextpad=0.3, handlelength=1.0,
                borderaxespad=0.15, borderpad=0.2,
            )
        else:
            axes.set_xticks([])
            axes.set_yticks([])
            axes.text(0.5, 0.5, 'Waiting for data', transform=axes.transAxes, ha='center', va='center', color='#b0b0c0')
        self.canvas.draw_idle()


class PageAMR(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  # Main 창 참조
        self.log_file_path = None  # 모니터링할 로그 파일 경로
        self.log_position = 0  # 마지막으로 읽은 파일 위치
        self.log_timer = QTimer()  # 로그 파일 감시 타이머
        self.log_timer.timeout.connect(self.update_log)  # 타이머 연결
        self.log_timer.timeout.connect(self.check_worker_exit)
        self.init_ui()
        self.communicator=None

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 제목
        title = QLabel('AMR')
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setFixedHeight(40)
        main_layout.addWidget(title)
        
        # 좌측 입력 영역과 우측 그래프·로그 영역
        splitter = QSplitter(Qt.Horizontal)
        
        # 좌측: 설계변수와 출력변수
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
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked | QAbstractItemView.AnyKeyPressed)
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
            }""")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
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
        self.output_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
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
        self.max_exp_spinbox = QDoubleSpinBox()
        self.max_exp_spinbox.setMinimum(1)
        self.max_exp_spinbox.setMaximum(10000)
        self.max_exp_spinbox.setValue(100)
        self.max_exp_spinbox.setDecimals(0)
        self.max_exp_spinbox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.max_exp_spinbox.setMinimumHeight(30)
        self.max_exp_spinbox.setFixedWidth(64)
        params_layout.addWidget(max_exp_label)
        params_layout.addWidget(self.max_exp_spinbox)
        
        # 수렴 종료 조건
        convergence_label = QLabel('수렴 종료:')
        self.convergence_spinbox = QDoubleSpinBox()
        self.convergence_spinbox.setMinimum(1)
        self.convergence_spinbox.setMaximum(1000)
        self.convergence_spinbox.setValue(10)
        self.convergence_spinbox.setDecimals(0)
        self.convergence_spinbox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.convergence_spinbox.setMinimumHeight(30)
        self.convergence_spinbox.setFixedWidth(64)
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
        scroll_area = QScrollArea()
        scroll_area.setWidget(left_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #1e1e1e;
                border: none;
            }""")
        scroll_area.setMinimumWidth(left_widget.minimumSizeHint().width() + scroll_area.verticalScrollBar().sizeHint().width())
        splitter.addWidget(scroll_area)
        
        # ===== 우측: 수렴 이력 + 실행 로그 =====
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)
        self.visualization_area = AMRConvergenceChart(right_widget)
        right_layout.addWidget(self.visualization_area, 2)
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(5)
        
        # 로그 모니터링 레이블
        log_label = QLabel('실행 로그')
        log_font = QFont()
        log_font.setPointSize(12)
        log_font.setBold(True)
        log_label.setFont(log_font)
        log_label.setFixedHeight(30)
        log_layout.addWidget(log_label)
        
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
        log_layout.addWidget(self.log_display, 1)
        right_layout.addWidget(log_widget, 1)
        splitter.addWidget(right_widget)
        
        # 스플리터 설정
        splitter.setCollapsible(0, False)  # 좌측 접기 불가
        splitter.setCollapsible(1, False)  # 우측 접기 불가
        splitter.setSizes([500, 500])
        main_layout.addWidget(splitter, 1)
        self.setLayout(main_layout)
        
    def stop_running(self):
        worker = getattr(self, 'amr_worker', None)
        if worker is None or not worker.is_alive():
            self.log_display.appendPlainText("중단할 AMR 프로세스가 없습니다.")
            return
        pid = worker.pid
        try:
            worker.terminate()
            worker.join(timeout=3)
        except (OSError, ValueError) as e:
            self.log_display.appendPlainText(f"AMR 프로세스 종료 실패 (PID: {pid}): {e}")
            return
        if worker.exitcode is None:
            self.log_display.appendPlainText(f"AMR 프로세스가 아직 종료되지 않았습니다 (PID: {pid}).")
            return
        self.update_log()
        self.log_timer.stop()
        self.visualization_area.finish()
        self.log_display.appendPlainText(f"AMR 프로세스 종료 확인 (PID: {pid}, 종료 코드: {worker.exitcode}).")

    def on_execute(self): # 실행 버튼 클릭 시 호출
        # Executing 플래그 확인
        if self.main_window.Executing is not None or (hasattr(self, 'amr_worker') and self.amr_worker.is_alive()):
            self.log_display.appendPlainText("이미 실행 중입니다.")
            return
        # Executing 상태 설정
        self.main_window.Executing = True
        try:
            amr.AMR_setting(self.main_window.WDIR)   # Task 폴더 초기화 작업 진행
            if self.log_timer.isActive(): # 이전 타이머 멈추기 (파일 handle이 해제되도록)
                self.log_timer.stop()

            log_file_path = os.path.join(self.main_window.WDIR, 'amrfunction.log')
            self.log_file_path = log_file_path
            self.log_position = 0  # 로그 위치 초기화
            self.log_display.clear()  # 로그 디스플레이 초기화
            max_exp = self.max_exp_spinbox.value()
            nx = len(self.main_window.DV)      # 선택된 설계 변수 개수
            nobj = 1
            ncon  = len(self.main_window.OV)-1
            xl = [float(self.table.item(i, 1).text()) for i in range(self.table.rowCount())]  # n x 1 list (하한값)
            xu = [float(self.table.item(i, 2).text()) for i in range(self.table.rowCount())]  # n x 1 list (상한값)
            xname = [self.table.item(i, 0).text() for i in range(self.table.rowCount())]  # n x 1 list (설계변수 이름)
            yname = [self.output_table.item(i, 0).text() for i in range(self.output_table.rowCount())]  # n x 1 list (출력변수 이름)
            unit= [self.table.item(i, 3).text() for i in range(self.table.rowCount())]  # n x 1 list (설계변수 단위)
            size_limit = int(max_exp)  # 최대 실험점 개수
            accuracy_limit =  [ov.get('TARGET_ERROR', 0)*0.01 for ov in self.main_window.OV]
            cpath=os.path.join(os.path.dirname(self.main_window.WDIR), 'task/AMR_Result')  # AMR 결과 저장 경로
            amr_logfile = Path(cpath) / 'AMR.LOG'
            amr_logfile.unlink(missing_ok=True)

            self.amr_worker = AMRWorker(
                nx=nx, nobj=nobj, ncon=ncon,
                xl=xl, xu=xu,
                size_limit=size_limit,
                accuracy_limit=accuracy_limit,
                cpath=cpath,
                opath=self.main_window.WDIR,
                rpm4fl=self.main_window.rpm4fl,
                ip=self.main_window.IP_ADDRESS,
                xname=xname,
                yname=yname,
                Unit=unit,
                what=self.main_window.ANALYSIS_TARGET,)
            self.amr_worker.start()
            self.visualization_area.follow_log(amr_logfile, yname)
            self.log_timer.start(1000)
            self.log_display.appendPlainText(f"AMR 프로세스 시작 (PID: {self.amr_worker.pid})")
        except Exception as e:
            self.log_display.appendPlainText(f"AMR 실행 준비 중 오류 발생: {e}")
        finally:
            self.main_window.Executing = None
    
    def check_worker_exit(self):
        worker = self.amr_worker
        exitcode = worker.exitcode
        if exitcode is None:
            return

        self.log_timer.stop()
        self.visualization_area.finish()
        if exitcode == 0:
            self.log_display.appendPlainText("========== 실행 완료 ==========")
        else:
            self.log_display.appendPlainText(f"AMR 실행 실패 (PID: {worker.pid}, 종료 코드: {exitcode}).")

    def on_browse_file(self): # 파일 탐색 버튼 클릭 시 호출
        file_path, _ = QFileDialog.getOpenFileName(self, '분석 결과 파일 선택', self.main_window.WDIR, 'CSV Files (*.csv);;All Files (*)')
        if file_path:
            self.info_path.setText(file_path)

    def on_execute2(self): # 작업 이어하기 실행 버튼 클릭 시 호출
        if self.main_window.Executing is not None or (hasattr(self, 'amr_worker') and self.amr_worker.is_alive()):
            self.log_display.appendPlainText("이미 실행 중입니다.")
            return
        info_path = self.info_path.text().strip()
        if not info_path:
            self.log_display.appendPlainText("오류: 이어하기 CSV 파일을 선택해주세요.")
            return
        if not os.path.isfile(info_path):
            self.log_display.appendPlainText(f"오류: 파일을 찾을 수 없습니다: {info_path}")
            return

        self.main_window.Executing = True
        try: # 이전 타이머 멈추기 (파일 handle이 해제되도록)
            if self.log_timer.isActive():
                self.log_timer.stop()
            log_file_path = os.path.join(self.main_window.WDIR, 'amrfunction.log')
            self.log_file_path = log_file_path
            self.log_position = 0  # 로그 위치 초기화
            self.log_display.clear()  # 로그 디스플레이 초기화
            max_exp = self.max_exp_spinbox.value()
            nx = len(self.main_window.DV)      # 선택된 설계 변수 개수
            nobj = 1
            ncon  = len(self.main_window.OV)-1
            xl = [float(self.table.item(i, 1).text()) for i in range(self.table.rowCount())]  # n x 1 list (하한값)
            xu = [float(self.table.item(i, 2).text()) for i in range(self.table.rowCount())]  # n x 1 list (상한값)
            xname = [self.table.item(i, 0).text() for i in range(self.table.rowCount())]  # n x 1 list (설계변수 이름)
            yname = [self.output_table.item(i, 0).text() for i in range(self.output_table.rowCount())]  # n x 1 list (출력변수 이름)
            unit= [self.table.item(i, 3).text() for i in range(self.table.rowCount())]  # n x 1 list (설계변수 단위)
            size_limit = int(max_exp)  # 최대 실험점 개수
            accuracy_limit =  [ov.get('TARGET_ERROR', 0)*0.01 for ov in self.main_window.OV]
            cpath=os.path.join(os.path.dirname(self.main_window.WDIR), 'task/AMR_Result')  # AMR 결과 저장 경로
            count_file = os.path.join(self.main_window.WDIR, 'runcount.txt')
            wdir_path = os.path.join(self.main_window.WDIR, 'wdir')
            if os.path.exists(wdir_path):
                folders = [d for d in os.listdir(wdir_path) if os.path.isdir(os.path.join(wdir_path, d)) and d.isdigit()]
                if folders:
                    max_folder_num = max(int(f) for f in folders)
                else:
                    max_folder_num = 0
            else:
                max_folder_num = 0

            with open(count_file, 'w') as f:
                f.write(str(max_folder_num))

            print(f"저장된 분석 파일에서 작업을 이어합니다: {info_path}")
            print(f"info_path = {info_path}")
            convergence_file = os.path.join(cpath, 'convergence_info.bin')
            amr_logfile = Path(cpath) / 'AMR.LOG'
            if os.path.exists(convergence_file):
                try:
                    os.remove(convergence_file)
                except OSError as e:
                    pass
            amr_logfile.unlink(missing_ok=True)
            self.amr_worker = AMRWorker(nx=nx, nobj=nobj, ncon=ncon,xl= xl,xu= xu, size_limit=size_limit,
                        accuracy_limit= accuracy_limit,cpath=cpath,opath=self.main_window.WDIR,rpm4fl=self.main_window.rpm4fl,
                        ip=self.main_window.IP_ADDRESS,xname=xname,yname=yname,Unit=unit, what=self.main_window.ANALYSIS_TARGET,restart=True, ppath=info_path
            )
            self.amr_worker.start()
            self.visualization_area.follow_log(amr_logfile, yname)
            self.log_timer.start(1000)
            self.log_display.appendPlainText(f"AMR 프로세스 시작 (PID: {self.amr_worker.pid})")
        except Exception as e:
            self.log_display.appendPlainText(f"AMR 실행 준비 중 오류 발생: {e}")
        finally:
            self.main_window.Executing = None
        

    def update_log(self): # 1초마다 로그 파일을 읽고 업데이트
        if not self.log_file_path or not os.path.exists(self.log_file_path):
            return
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f: # 마지막으로 읽은 위치에서 시작
                f.seek(self.log_position)
                new_content = f.read()
                if new_content:
                    self.log_display.appendPlainText(new_content.rstrip()) # 새로운 로그 내용을 디스플레이에 추가
                    self.log_position = f.tell() # 현재 파일 위치 저장
                    self.log_display.verticalScrollBar().setValue(self.log_display.verticalScrollBar().maximum()) # 자동 스크롤: 항상 마지막 줄이 보이도록
        except Exception as e:
            print(f"로그 파일 읽기 오류: {e}")
    
    def refresh_table(self): # Main page에서 호출: DV와 OV 데이터로 테이블 업데이트
        if self.main_window.DV: # 설계 변수 테이블 업데이트
            self.table.setRowCount(len(self.main_window.DV))
            for i, item in enumerate(self.main_window.DV):
                self.table.setRowHeight(i, 35)
                name = item.get('NAME', '')
                unit = item.get('UNIT', '')
                lv = item.get('LV', 0)  # 하한값
                uv = item.get('UV', 0)  # 상한값
                self.table.setItem(i, 0, QTableWidgetItem(name)) # 0열: 설계변수 (NAME)
                self.table.setItem(i, 1, QTableWidgetItem(f'{lv:.3f}')) # 1열: 하한값 (LV)
                self.table.setItem(i, 2, QTableWidgetItem(f'{uv:.3f}')) # 2열: 상한값 (UV)
                self.table.setItem(i, 3, QTableWidgetItem(unit)) # 3열: 단위 (UNIT)
        else:
            self.table.setRowCount(0) # DV가 비어있으면 테이블 초기화
        
        
        if self.main_window.OV: # 출력 변수 테이블 업데이트
            self.output_table.setRowCount(len(self.main_window.OV))
            for i, item in enumerate(self.main_window.OV):
                self.output_table.setRowHeight(i, 35)
                name = item.get('NAME', '')
                target_error = item.get('TARGET_ERROR', '')
                self.output_table.setItem(i, 0, QTableWidgetItem(name)) # 0열: 출력변수 (NAME)
                self.output_table.setItem(i, 1, QTableWidgetItem(str(target_error))) # 1열: 목표 오차율 (정수/실수를 문자열로 변환) ### 2열: 생성여부 (콤보박스 - 읽기 전용으로 표시)
                label = QLabel('선택됨')
                self.output_table.setCellWidget(i, 2, label)
        else:
            self.output_table.setRowCount(0) # OV가 비어있으면 테이블 초기화