import os

from PySide6.QtWidgets import QWidget, QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QAbstractItemView, QHBoxLayout, QPushButton, QPlainTextEdit, QSplitter, QComboBox, QLineEdit, QFileDialog
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
import functions.do_functions as do
import multiprocessing as mp 
import numpy as np 
from aGO.core.base import *
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.termination import get_termination
from pymoo.optimize import minimize

class DOworker(mp.Process):
    def __init__(self, DV_info,output_info,meta_path, result_connection):
        super().__init__()
        self.DV_info = DV_info
        self.output_info = output_info
        self.meta_path = meta_path
        self.result_connection = result_connection

    def run(self):
        """워커 스레드에서 실행될 코드"""
        nobj = 0 
        for item in self.output_info:
            if item.get('objective_type') in ['목적함수(최대화)', '목적함수(최소화)']:
                nobj += 1

        if nobj ==1:
            temp = do.DO(DV_info=self.DV_info, output_info=self.output_info,meta_path=self.meta_path)
            logfile=os.path.join(self.meta_path,'aGO.log')
            
            if os.path.exists(logfile):
                try:
                    os.remove(logfile)
                except OSError as e:
                    pass
            # logfile이 존재하면 삭제
            if os.path.exists(logfile):
                try:
                    os.remove(logfile)
                except OSError as e:
                    pass
            try:
                # Task 생성 및 저장 
                aGO_Opt = aGO(ndv=temp.ndv, 
                            ncon=temp.ncon ,
                            xl=temp.LB, 
                            xu=temp.UB, 
                            obj=temp.obj,
                            con=temp.con, 
                            DisLvX=temp.DisLvX, 
                            DisSetX=temp.DisSetX,
                            iStopEval =3000,
                            nPop_DE   = 30,
                            nPop_CS   = 15,
                            iTRMOP    = 10000,
                            cpath=self.meta_path)
                if temp.ncon==0:
                    Xopt, OBJopt = aGO_Opt.run()
                    CONopt = None
                else:
                    Xopt, OBJopt, CONopt =aGO_Opt.run()
                print("Xopt:", Xopt)
                print("OBJopt:", OBJopt)
                print("CONopt:", CONopt)
                # Task 실행 완료 대기
                #self.log_display.appendPlainText("Task finished")
                

                initialx = np.array([(ub + lb) * 0.5 for ub, lb in zip(temp.UB, temp.LB)])
                initialf= temp.obj(initialx)
                initialg = temp.G 

                with open(logfile, 'a', encoding='utf-8') as f:
                    f.write("[Design Variables]\n")
                    for dv_item in self.DV_info:
                        f.write(f"{dv_item}\n")
                    f.write("\n[Output Variables]\n")
                    for output_item in self.output_info:
                        f.write(f"{output_item}\n")
                    f.write("\n[Initial Values]\n")
                    f.write(f"initialf: {initialf}\n")
                    f.write(f"initialg: {initialg}\n")  
                    f.write("\n[Optimum Values]\n")
                    f.write(f"temp.obj: {temp.optobj}\n")
                    f.write(f"temp.con: {temp.optcon}\n")
            except Exception as e:
                #self.log_display.appendPlainText(f"Error: {str(e)}")
                print(f"Error: {str(e)}")

        else:    
            temp=do.MOGA(DV_info=self.DV_info, output_info=self.output_info, meta_path=self.meta_path)
            algorithm = NSGA2(
                pop_size=40,
                n_offsprings=10,
                sampling=FloatRandomSampling(),
                crossover=SBX(prob=0.9, eta=15),
                mutation=PM(eta=20),
                eliminate_duplicates=True
            )          
            termination = get_termination("n_gen", 100)

            res = minimize(
                problem=temp,
                algorithm=algorithm,
                termination=termination,
                seed=1,
                save_history=True,
                verbose=True
            )
            F = res.F
            if F is None or np.ndim(F) != 2 or F.shape[0] == 0 or F.shape[1] < 2:
                raise ValueError("표시할 다목적 최적화 결과가 없습니다.")
            self.result_connection.send(F[:, :2].tolist())
            self.result_connection.close()

    def stop(self): 
        """프로세스 종료"""
        if self.is_alive():
            self.terminate()

class ObjectiveScatterDialog(QDialog):
    def __init__(self, points, objectives, parent=None):
        super().__init__(parent)
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
        from matplotlib.figure import Figure

        self.setWindowTitle("Objective Space")
        self.resize(800, 600)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        figure = Figure(layout='constrained')
        self.canvas = FigureCanvasQTAgg(figure)
        self.axes = figure.add_subplot()
        self.points = np.asarray(points, dtype=float)
        self.scatter = self.axes.scatter(
            self.points[:, 0], self.points[:, 1],
            s=30, facecolors='none', edgecolors='blue',
        )
        self.axes.set_title("Objective Space")
        labels = []
        for objective in objectives[:2]:
            label = objective['name']
            if objective['objective_type'] == '목적함수(최대화)':
                label += ' (최적화 값: -원래 값)'
            labels.append(label)
        self.axes.set_xlabel(labels[0])
        self.axes.set_ylabel(labels[1])
        self.annotation = self.axes.annotate(
            '', xy=(0, 0), xytext=(10, 10), textcoords='offset points',
            bbox=dict(boxstyle='round', fc='white', alpha=0.9),
        )
        self.annotation.set_visible(False)
        self.canvas.mpl_connect('motion_notify_event', self.on_hover)
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)

    def on_hover(self, event):
        if event.inaxes == self.axes:
            contains, details = self.scatter.contains(event)
            if contains:
                indices = details['ind']
                screen_points = self.axes.transData.transform(self.points[indices])
                nearest = np.argmin(np.sum((screen_points - [event.x, event.y]) ** 2, axis=1))
                x, y = self.points[indices[nearest]]
                self.annotation.xy = (x, y)
                self.annotation.set_text(f'({x:.6g}, {y:.6g})')
                self.annotation.set_visible(True)
                self.canvas.draw_idle()
                return
        if self.annotation.get_visible():
            self.annotation.set_visible(False)
            self.canvas.draw_idle()


class PageDO(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  # Main 창 참조
        self.result_connection = None
        self.scatter_dialogs = []
        self.worker_timer = QTimer(self)
        self.worker_timer.timeout.connect(self.check_worker)
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 제목
        title = QLabel('DO')
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

        
        # 설계 변수 정보 텍스트 + 메타모델 경로 입력 부분
        design_var_header_layout = QHBoxLayout()
        design_var_label = QLabel('확정된 설계 변수')
        design_var_font = QFont()
        design_var_font.setPointSize(12)
        design_var_font.setBold(True)
        design_var_label.setFont(design_var_font)
        design_var_header_layout.addWidget(design_var_label)
        
        # 메타모델 폴더 경로 입력창
        self.metamodel_path_input = QLineEdit()
        self.metamodel_path_input.setPlaceholderText('메타모델 폴더 경로')
        self.metamodel_path_input.setMaximumWidth(300)
        self.metamodel_path_input.setMinimumHeight(50)
        design_var_header_layout.addWidget(self.metamodel_path_input)
        
        # 폴더 탐색 버튼
        btn_browse = QPushButton('탐색')
        btn_browse.setMaximumWidth(80)
        btn_browse.setMinimumHeight(50)
        btn_browse.clicked.connect(self.browse_metamodel_folder)
        design_var_header_layout.addWidget(btn_browse)
        
        # 메타모델 적용 버튼
        btn_apply_metamodel = QPushButton('메타모델 적용')
        btn_apply_metamodel.setMaximumWidth(120)
        btn_apply_metamodel.setMinimumHeight(50)
        btn_apply_metamodel.clicked.connect(self.on_metaload)
        design_var_header_layout.addWidget(btn_apply_metamodel)
        
        design_var_header_layout.addStretch()
        
        design_var_header_widget = QWidget()
        design_var_header_widget.setLayout(design_var_header_layout)
        design_var_header_widget.setFixedHeight(70)
        left_layout.addWidget(design_var_header_widget)
        
        # 테이블 생성 (5 x n: NAME, 하한값, 상한값, 단위, 불연속 변수 SET)
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['설계변수', '하한 값', '상한 값', '단위', '불연속 변수 SET'])
        
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
        
        # 열 너비 설정 (5번째 열: 앞의 3개 열 너비의 합)
        # 기본 너비: 설계변수(120) + 하한값(120) + 상한값(120) = 360
        self.table.setColumnWidth(0, 120)  # 설계변수
        self.table.setColumnWidth(1, 120)  # 하한 값
        self.table.setColumnWidth(2, 120)  # 상한 값
        self.table.setColumnWidth(4, 360)  # 불연속 변수 SET (앞 3개 열의 합)
        
        left_layout.addWidget(self.table, 1)
        
        # 출력 변수 레이블
        output_var_label = QLabel('확정된 출력 변수')
        output_var_font = QFont()
        output_var_font.setPointSize(12)
        output_var_font.setBold(True)
        output_var_label.setFont(output_var_font)
        output_var_label.setFixedHeight(30)
        left_layout.addWidget(output_var_label)
        
        # 출력 변수 테이블 생성 (4열: NAME, 목적함수/구속조건, 구속조건 하한값, 구속조건 상한값)
        self.output_table = QTableWidget()
        self.output_table.setColumnCount(4)
        self.output_table.setHorizontalHeaderLabels(['출력변수', '목적함수/구속조건', '구속조건 하한값', '구속조건 상한값','사용안함'])
        
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
            QComboBox {
                background-color: #3d3d3d;
                color: #e0e0e0;
                border: 1px solid #0d47a1;
            }
            QDoubleSpinBox {
                background-color: #3d3d3d;
                color: #e0e0e0;
                border: 1px solid #0d47a1;
            }
        """)
        
        # 열 너비 설정 (20% 증가)
        self.output_table.setColumnWidth(0, 156)  # 출력변수
        self.output_table.setColumnWidth(1, 180)  # 목적함수/구속조건
        self.output_table.setColumnWidth(2, 180)  # 구속조건 하한값
        self.output_table.setColumnWidth(3, 180)  # 구속조건 상한값
        
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
        if self.worker_timer.isActive():
            self.monitor_display.appendPlainText("이미 최적화가 실행 중입니다.")
            return
        # 설계 변수 테이블에서 정보 수집
        DV_info = []
        for i in range(self.table.rowCount()):
            dv_item = {
                'name': self.table.item(i, 0).text(),
                'lv': float(self.table.item(i, 1).text()),
                'uv': float(self.table.item(i, 2).text()),
                'unit': self.table.item(i, 3).text(),
                'discrete_set': self.table.item(i, 4).text() if self.table.item(i, 4) else ''
            }
            DV_info.append(dv_item)

        
        # 출력 변수 테이블에서 정보 수집
        output_info = []
        for i in range(self.output_table.rowCount()):
            # 0열: 출력변수 이름
            output_name = self.output_table.item(i, 0).text()
            
            # 1열: 목적함수/구속조건 선택 (ComboBox)
            combo_widget = self.output_table.cellWidget(i, 1)
            objective_type = combo_widget.currentText() if combo_widget else ''
            
            # 2열: 구속조건 하한값 (QLineEdit)
            lower_widget = self.output_table.cellWidget(i, 2)
            lower_bound = float(lower_widget.text()) if lower_widget and lower_widget.text() else None
            
            # 3열: 구속조건 상한값 (QLineEdit)
            upper_widget = self.output_table.cellWidget(i, 3)
            upper_bound = float(upper_widget.text()) if upper_widget and upper_widget.text() else None
            
            output_item = {
                'name': output_name,
                'objective_type': objective_type,
                'lower_bound': lower_bound,
                'upper_bound': upper_bound
            }
            output_info.append(output_item)
        

        metapath=self.metamodel_path_input.text()

        objectives = [item for item in output_info if item['objective_type'] in ('목적함수(최대화)', '목적함수(최소화)')]
        if not objectives:
            self.monitor_display.appendPlainText("최소 1개의 목적함수를 선택해주세요.")
            return
        self.objectives = objectives
        receiver, sender = mp.Pipe(duplex=False)
        self.temp =DOworker(DV_info=DV_info, output_info=output_info,meta_path=metapath, result_connection=sender)
        #temp = do.DO(DV_info=DV_info, output_info=output_info,meta_path=metapath)
        import numpy as np


        # logfile에 DV_item, output_item, initialf, initialg 기록

        try:
            self.temp.start()
            sender.close()
            self.result_connection = receiver
            self.worker_timer.start(200)
        except Exception as e:
            sender.close()
            receiver.close()
            self.monitor_display.appendPlainText(f"DO 구성 실패: {e}")
            print(f"DO 구성 실패 : {e}")
       # aGO_Opt = aGO(ndv=temp.ndv, ncon=temp.ncon ,xl=temp.LB, xu=temp.UB, obj=temp.obj,con=temp.con, DisLvX=temp.DisLvX, DisSetX=temp.DisSetX,iStopEval =3000,nPop_DE   = 30,nPop_CS   = 15,iTRMOP    = 10000,cpath=metapath)

        

    
    def check_worker(self):
        exitcode = self.temp.exitcode
        if self.result_connection is not None and self.result_connection.poll():
            try:
                points = self.result_connection.recv()
            except EOFError:
                points = None
            finally:
                self.result_connection.close()
                self.result_connection = None
            if points is not None:
                dialog = ObjectiveScatterDialog(points, self.objectives, self)
                self.scatter_dialogs.append(dialog)
                dialog.finished.connect(lambda _, window=dialog: self.scatter_dialogs.remove(window))
                dialog.show()

        if exitcode is not None:
            self.temp.join()
            self.worker_timer.stop()
            if self.result_connection is not None:
                self.result_connection.close()
                self.result_connection = None
            if exitcode != 0:
                self.monitor_display.appendPlainText(
                    f"최적화 실행 실패 (종료 코드: {exitcode})."
                )

    def browse_metamodel_folder(self):
        """폴더 탐색 버튼 클릭 시 호출"""
        folder_path = QFileDialog.getExistingDirectory(self, '메타모델 폴더 선택')
        if folder_path:
            self.metamodel_path_input.setText(folder_path)
    
    def on_metaload(self):
        """메타모델 적용 버튼 클릭 시 호출"""
        metamodel_path = self.metamodel_path_input.text()
        if not metamodel_path:
            print("메타모델 폴더 경로를 입력해주세요.")
            return
        
        # 메타모델 로드 및 변수명 추출
        dv_list, out_list = do.meta_ParseV(metamodel_path)
        
        # 설계 변수 테이블 업데이트 (column 0만)
        if dv_list:
            self.table.setRowCount(len(dv_list))
            for i, var_name in enumerate(dv_list):
                self.table.setRowHeight(i, 35)
                # Column 0: 변수명만 업데이트
                self.table.setItem(i, 0, QTableWidgetItem(var_name))
                # 나머지 열은 빈 상태로 유지
                self.table.setItem(i, 1, QTableWidgetItem(''))
                self.table.setItem(i, 2, QTableWidgetItem(''))
                self.table.setItem(i, 3, QTableWidgetItem(''))
                self.table.setItem(i, 4, QTableWidgetItem(''))
        
        # 출력 변수 테이블 업데이트 (column 0만)
        if out_list:
            self.output_table.setRowCount(len(out_list))
            for i, var_name in enumerate(out_list):
                self.output_table.setRowHeight(i, 35)
                # Column 0: 변수명만 업데이트
                self.output_table.setItem(i, 0, QTableWidgetItem(var_name))
                # 나머지 열은 위젯으로 초기화
                combo_box = QComboBox()
                combo_box.addItems(['목적함수(최소화)', '목적함수(최대화)', '구속조건', '사용안함'])
                combo_box.setStyleSheet("""
                    QComboBox {
                        background-color: #3d3d3d;
                        color: #e0e0e0;
                        border: 1px solid #0d47a1;
                        padding: 2px;
                    }
                    QComboBox::drop-down {
                        border: none;
                    }
                    QComboBox QAbstractItemView {
                        background-color: #2d2d2d;
                        color: #e0e0e0;
                        selection-background-color: #0d47a1;
                    }
                """)
                self.output_table.setCellWidget(i, 1, combo_box)
                
                # Column 2: 하한값
                lower_input = QLineEdit()
                lower_input.setPlaceholderText('')
                lower_input.setStyleSheet("""
                    QLineEdit {
                        background-color: #3d3d3d;
                        color: #e0e0e0;
                        border: 1px solid #0d47a1;
                        padding: 2px;
                    }
                """)
                self.output_table.setCellWidget(i, 2, lower_input)
                
                # Column 3: 상한값
                upper_input = QLineEdit()
                upper_input.setPlaceholderText('')
                upper_input.setStyleSheet("""
                    QLineEdit {
                        background-color: #3d3d3d;
                        color: #e0e0e0;
                        border: 1px solid #0d47a1;
                        padding: 2px;
                    }
                """)
                self.output_table.setCellWidget(i, 3, upper_input)
