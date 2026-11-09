import shutil
import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QComboBox, QAbstractItemView, QMenu, QPushButton, QHBoxLayout, QLineEdit, QFileDialog, QSpinBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from functions.main_functions import load_IV_list, load_OV_list, Analysis_setting, create_save, create_load


class PageMain(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  # Main 창 참조
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # IV_list 로드 (Main 창에 저장)
        self.main_window.IV_list = load_IV_list()
        
        # OV_list 로드 (Main 창에 저장)
        self.main_window.OV_list = load_OV_list()
        
        # 제목
        title = QLabel('Multi-Physics Software - Main')
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setFixedHeight(40)
        main_layout.addWidget(title)
        
        # 프로젝트 저장/불러오기 버튼 레이아웃
        project_button_layout = QHBoxLayout()
        project_button_layout.setSpacing(10)
        
        btn_save = QPushButton('프로젝트 저장')
        btn_save.setMinimumHeight(30)
        btn_save.setMaximumWidth(120)
        btn_save.clicked.connect(self.on_save)
        project_button_layout.addWidget(btn_save)
        
        btn_load = QPushButton('프로젝트 불러오기')
        btn_load.setMinimumHeight(30)
        btn_load.setMaximumWidth(120)
        btn_load.clicked.connect(self.on_load)
        project_button_layout.addWidget(btn_load)
        
        project_button_layout.addStretch()
        
        main_layout.addLayout(project_button_layout)
        
        # 설계 변수 설정 텍스트
        design_var_label = QLabel('설계 변수 설정')
        design_var_font = QFont()
        design_var_font.setPointSize(12)
        design_var_font.setBold(True)
        design_var_label.setFont(design_var_font)
        design_var_label.setFixedHeight(30)
        main_layout.addWidget(design_var_label)
        
        # N x 5 테이블 생성
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['입력변수', '하한 값', '상한 값', '단위', '선택여부'])
        
        # 우클릭 메뉴 활성화
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # 엑셀처럼 편집 가능하도록 설정
        self.table.setEditTriggers(
            QAbstractItemView.DoubleClicked |
            QAbstractItemView.SelectedClicked |
            QAbstractItemView.AnyKeyPressed
        )
        
        # 테이블 에디터 폰트 설정
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
            }
            QTableWidget QComboBox {
                font-size: 12px;
                padding: 3px;
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
        
        # IV_list 데이터로 테이블 생성
        if self.main_window.IV_list:
            self.add_table_rows_from_IV_list()
        else:
            self.add_table_rows(5)
        
        # 입력 변수 테이블을 상단 50%에 배치
        main_layout.addWidget(self.table, 1)
        
        # 출력 변수 레이블
        output_var_label = QLabel('출력 변수 설정')
        output_var_font = QFont()
        output_var_font.setPointSize(12)
        output_var_font.setBold(True)
        output_var_label.setFont(output_var_font)
        output_var_label.setFixedHeight(30)
        main_layout.addWidget(output_var_label)
        
        # N x 3 테이블 생성 (출력 변수)
        self.output_table = QTableWidget()
        self.output_table.setColumnCount(3)
        self.output_table.setHorizontalHeaderLabels(['출력변수', '목표 오차율(%)', '생성여부'])
        
        # 우클릭 메뉴 활성화
        self.output_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.output_table.customContextMenuRequested.connect(self.show_output_context_menu)
        
        # 엑셀처럼 편집 가능하도록 설정
        self.output_table.setEditTriggers(
            QAbstractItemView.DoubleClicked |
            QAbstractItemView.SelectedClicked |
            QAbstractItemView.AnyKeyPressed
        )
        
        # 출력 테이블 스타일 설정
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
            QTableWidget QLineEdit {
                font-size: 12px;
                padding: 4px;
            }
            QTableWidget QComboBox {
                font-size: 12px;
                padding: 3px;
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
        
        # OV_list 데이터로 테이블 생성
        if self.main_window.OV_list:
            self.add_output_table_rows_from_OV_list()
        else:
            self.add_output_table_rows(5)
        
        # 출력 변수 테이블을 하단 50%에 배치
        main_layout.addWidget(self.output_table, 1)
        
        # 해석 결과 폴더 선택 레이아웃
        result_layout = QHBoxLayout()
        result_layout.setSpacing(10)
        
        result_label = QLabel('해석 결과 폴더:')
        result_label.setFixedWidth(100)
        result_layout.addWidget(result_label)
        
        self.result_folder_input = QLineEdit()
        self.result_folder_input.setPlaceholderText('폴더 경로를 입력하거나 버튼으로 선택...')
        self.result_folder_input.setMinimumHeight(30)
        result_layout.addWidget(self.result_folder_input)
        
        btn_browse = QPushButton('폴더 탐색')
        btn_browse.setMinimumHeight(30)
        btn_browse.setMaximumWidth(100)
        btn_browse.clicked.connect(self.on_browse_folder)
        result_layout.addWidget(btn_browse)
        
        main_layout.addLayout(result_layout)
        
        # 의왕 서버 레이아웃
        uiwang_layout = QHBoxLayout()
        uiwang_layout.setSpacing(10)
        
        # 의왕 서버 IP
        uiwang_ip_label = QLabel('파주 서버 IP:')
        uiwang_ip_label.setFixedWidth(100)
        uiwang_layout.addWidget(uiwang_ip_label)
        
        self.uiwang_ip_input = QLineEdit()
        self.uiwang_ip_input.setPlaceholderText('파주 서버 IP 입력...')
        self.uiwang_ip_input.setMinimumHeight(30)
        self.uiwang_ip_input.setMaximumWidth(150)
        uiwang_layout.addWidget(self.uiwang_ip_input)
        
        # 의왕 노드개수
        uiwang_node_label = QLabel('노드개수:')
        uiwang_node_label.setFixedWidth(80)
        uiwang_layout.addWidget(uiwang_node_label)
        
        self.uiwang_node_input = QSpinBox()
        self.uiwang_node_input.setMinimum(0)
        self.uiwang_node_input.setMaximum(999)
        self.uiwang_node_input.setValue(1)
        self.uiwang_node_input.setMinimumHeight(30)
        self.uiwang_node_input.setMaximumWidth(100)
        uiwang_layout.addWidget(self.uiwang_node_input)
        
        uiwang_layout.addStretch()
        
        main_layout.addLayout(uiwang_layout)
        
        # 광주 서버 레이아웃
        gwangju_layout = QHBoxLayout()
        gwangju_layout.setSpacing(10)
        
        # 광주 서버 IP
        gwangju_ip_label = QLabel('광주 서버 IP:')
        gwangju_ip_label.setFixedWidth(100)
        gwangju_layout.addWidget(gwangju_ip_label)
        
        self.gwangju_ip_input = QLineEdit()
        self.gwangju_ip_input.setPlaceholderText('광주 서버 IP 입력...')
        self.gwangju_ip_input.setMinimumHeight(30)
        self.gwangju_ip_input.setMaximumWidth(150)
        gwangju_layout.addWidget(self.gwangju_ip_input)
        
        # 광주 노드개수
        gwangju_node_label = QLabel('노드개수:')
        gwangju_node_label.setFixedWidth(80)
        gwangju_layout.addWidget(gwangju_node_label)
        
        self.gwangju_node_input = QSpinBox()
        self.gwangju_node_input.setMinimum(0)
        self.gwangju_node_input.setMaximum(999)
        self.gwangju_node_input.setValue(1)
        self.gwangju_node_input.setMinimumHeight(30)
        self.gwangju_node_input.setMaximumWidth(100)
        gwangju_layout.addWidget(self.gwangju_node_input)
        
        gwangju_layout.addStretch()
        
        main_layout.addLayout(gwangju_layout)
        
        # rpm4fl 및 해석 대상 입력 레이아웃
        analysis_layout = QHBoxLayout()
        analysis_layout.setSpacing(10)
        
        # rpm4fl
        rpm4fl_label = QLabel('rpm4fl:')
        rpm4fl_label.setFixedWidth(120)
        analysis_layout.addWidget(rpm4fl_label)
        
        self.rpm4fl_input = QLineEdit()
        self.rpm4fl_input.setPlaceholderText('rpm4fl 입력...')
        self.rpm4fl_input.setMinimumHeight(30)
        self.rpm4fl_input.setMaximumWidth(100)
        if self.main_window.rpm4fl:
            self.rpm4fl_input.setText(self.main_window.rpm4fl)
        else:
            self.rpm4fl_input.setText('100')  # 기본값 설정
        analysis_layout.addWidget(self.rpm4fl_input)

        # 해석 대상
        analysis_target_label = QLabel('해석 대상:')
        analysis_target_label.setFixedWidth(80)
        analysis_layout.addWidget(analysis_target_label)
        
        self.analysis_target_combo = QComboBox()
        self.analysis_target_combo.addItems(['All', 'Mechanical', 'Maxwell'])
        self.analysis_target_combo.setMinimumHeight(30)
        self.analysis_target_combo.setMaximumWidth(150)
        if self.main_window.ANALYSIS_TARGET:
            self.analysis_target_combo.setCurrentText(self.main_window.ANALYSIS_TARGET)
        analysis_layout.addWidget(self.analysis_target_combo)
        
        analysis_layout.addStretch()
        
        main_layout.addLayout(analysis_layout)
        
        self.setLayout(main_layout)
        
        # 하단 버튼 레이아웃 (좌측)
        button_layout = QHBoxLayout()
        
        btn_confirm = QPushButton('설계변수 확정')
        btn_confirm.setMinimumHeight(40)
        btn_confirm.setMaximumWidth(150)
        btn_confirm.clicked.connect(self.on_confirm_design_variables)
        button_layout.addWidget(btn_confirm)
        
        button_layout.addStretch()  # 나머지 공간 채우기
        
        main_layout.addLayout(button_layout)
    def add_table_rows_from_IV_list(self):
        """IV_list 데이터를 기반으로 테이블 행 추가"""
        row_count = len(self.main_window.IV_list)
        self.table.setRowCount(row_count)
        
        for i, item in enumerate(self.main_window.IV_list):
            # 행 높이 설정
            self.table.setRowHeight(i, 35)
            
            name = item.get('NAME', '')
            unit = item.get('UNIT', '')
            value = item.get('Value', 0)
            
            # 상한값: Value의 110%
            upper_limit = value * 1.1
            # 하한값: Value의 90%
            lower_limit = value * 0.9
            
            # 0열: 입력변수 (NAME)
            self.table.setItem(i, 0, QTableWidgetItem(name))
            # 1열: 하한값 (Value의 90%)
            #self.table.setItem(i, 1, QTableWidgetItem(f'{lower_limit:.3f}'))
            # 2열: 상한값 (Value의 110%)
            #self.table.setItem(i, 2, QTableWidgetItem(f'{upper_limit:.3f}'))
            # 3열: 단위 (UNIT)
            self.table.setItem(i, 3, QTableWidgetItem(unit))
            
            # 4열: 선택여부 (콤보박스)
            combo_box = QComboBox()
            combo_box.addItems(['선택', '선택안함'])
            combo_box.setCurrentText('선택안함')
            combo_box.setStyleSheet("""
                QComboBox {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 1px solid #0d47a1;
                    border-radius: 3px;
                    padding: 3px;
                    font-size: 12px;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 20px;
                }
            """)
            self.table.setCellWidget(i, 4, combo_box)
    
    def add_table_rows(self, row_count):
        """테이블에 행 추가"""
        current_row = self.table.rowCount()
        self.table.setRowCount(current_row + row_count)
        
        for i in range(current_row, current_row + row_count):
            # 행 높이 설정
            self.table.setRowHeight(i, 35)
            
            self.table.setItem(i, 0, QTableWidgetItem(f'파라미터_{i+1}'))
            self.table.setItem(i, 1, QTableWidgetItem(f'{10 * (i+1)}'))
            self.table.setItem(i, 2, QTableWidgetItem(f'{20 * (i+1)}'))
            self.table.setItem(i, 3, QTableWidgetItem(f'{30 * (i+1)}'))
            
            # 콤보박스 적용
            combo_box = QComboBox()
            combo_box.addItems(['선택', '선택안함'])
            combo_box.setCurrentText('선택안함')
            combo_box.setStyleSheet("""
                QComboBox {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 1px solid #0d47a1;
                    border-radius: 3px;
                    padding: 3px;
                    font-size: 12px;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 20px;
                }
            """)
            self.table.setCellWidget(i, 4, combo_box)
    
    def add_output_table_rows_from_OV_list(self):
        """OV_list 데이터를 기반으로 출력 테이블 행 추가"""
        row_count = len(self.main_window.OV_list)
        self.output_table.setRowCount(row_count)
        
        for i, item in enumerate(self.main_window.OV_list):
            # 행 높이 설정
            self.output_table.setRowHeight(i, 35)
            
            name = item.get('NAME', '')
            target_error = item.get('TARGET_ERROR', '')
            
            # 0열: 출력변수 (NAME)
            self.output_table.setItem(i, 0, QTableWidgetItem(name))
            # 1열: 목표 오차율 (정수/실수를 문자열로 변환)
            self.output_table.setItem(i, 1, QTableWidgetItem(str(target_error)))
            
            # 2열: 생성여부 (콤보박스)
            combo_box = QComboBox()
            combo_box.addItems(['선택', '선택안함'])
            combo_box.setCurrentText('선택안함')
            combo_box.setStyleSheet("""
                QComboBox {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 1px solid #0d47a1;
                    border-radius: 3px;
                    padding: 3px;
                    font-size: 12px;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 20px;
                }
            """)
            self.output_table.setCellWidget(i, 2, combo_box)
    
    def add_output_table_rows(self, row_count):
        """출력 테이블에 행 추가"""
        current_row = self.output_table.rowCount()
        self.output_table.setRowCount(current_row + row_count)
        
        for i in range(current_row, current_row + row_count):
            # 행 높이 설정
            self.output_table.setRowHeight(i, 35)
            
            self.output_table.setItem(i, 0, QTableWidgetItem(f'출력변수_{i+1}'))
            self.output_table.setItem(i, 1, QTableWidgetItem(f'{0.01 * (i+1)}'))
            
            # 콤보박스 적용
            combo_box = QComboBox()
            combo_box.addItems(['선택', '선택안함'])
            combo_box.setCurrentText('선택안함')
            combo_box.setStyleSheet("""
                QComboBox {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 1px solid #0d47a1;
                    border-radius: 3px;
                    padding: 3px;
                    font-size: 12px;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 20px;
                }
            """)
            self.output_table.setCellWidget(i, 2, combo_box)
    
    def show_context_menu(self, position):
        """우클릭 메뉴 표시"""
        menu = QMenu(self.table)
        
        select_action = menu.addAction('선택')
        select_action.triggered.connect(lambda: self.set_selection_status('선택'))
        
        not_select_action = menu.addAction('선택안함')
        not_select_action.triggered.connect(lambda: self.set_selection_status('선택안함'))
        
        menu.exec(self.table.mapToGlobal(position))
    
    def set_selection_status(self, status):
        """선택된 행들의 선택여부를 일괄 변경"""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
        
        for row in selected_rows:
            combo_box = self.table.cellWidget(row, 4)
            if isinstance(combo_box, QComboBox):
                combo_box.setCurrentText(status)
    
    def show_output_context_menu(self, position):
        """출력 테이블 우클릭 메뉴 표시"""
        menu = QMenu(self.output_table)
        
        select_action = menu.addAction('선택')
        select_action.triggered.connect(lambda: self.set_output_selection_status('선택'))
        
        not_select_action = menu.addAction('선택안함')
        not_select_action.triggered.connect(lambda: self.set_output_selection_status('선택안함'))
        
        menu.exec(self.output_table.mapToGlobal(position))
    
    def set_output_selection_status(self, status):
        """출력 테이블의 선택된 행들의 생성여부를 일괄 변경"""
        selected_rows = set()
        for item in self.output_table.selectedItems():
            selected_rows.add(item.row())
        
        for row in selected_rows:
            combo_box = self.output_table.cellWidget(row, 2)
            if isinstance(combo_box, QComboBox):
                combo_box.setCurrentText(status)
    
    def on_confirm_design_variables(self):
        """설계변수 확정 버튼 클릭 시 호출"""
        # 선택된 설계 변수 정보 추출
        self.main_window.DV = []
        for row in range(self.table.rowCount()):
            combo_box = self.table.cellWidget(row, 4)
            if isinstance(combo_box, QComboBox) and combo_box.currentText() == '선택':
                try:
                    dv_item = {
                        'NAME': self.table.item(row, 0).text(),
                        'LV': float(self.table.item(row, 1).text()),
                        'UV': float(self.table.item(row, 2).text()),
                        'UNIT': self.table.item(row, 3).text()
                    }
                    self.main_window.DV.append(dv_item)
                except (ValueError, AttributeError):
                    print(f"설계 변수 정보 추출 중 오류 발생: 행 {row+1}의 데이터가 올바르지 않습니다.")
                    return
        
        # 선택된 출력 변수 정보 추출
        self.main_window.OV = []
        for row in range(self.output_table.rowCount()):
            combo_box = self.output_table.cellWidget(row, 2)
            if isinstance(combo_box, QComboBox) and combo_box.currentText() == '선택':
                try:
                    ov_item = {
                        'NAME': self.output_table.item(row, 0).text(),
                        'TARGET_ERROR': float(self.output_table.item(row, 1).text())
                    }
                    self.main_window.OV.append(ov_item)
                except (ValueError, AttributeError):
                    pass
        # 슈퍼컴 서버 정보 기록 
        supercom = []
        supercom.extend([self.uiwang_ip_input.text()] * self.uiwang_node_input.value())
        supercom.extend([self.gwangju_ip_input.text()] * self.gwangju_node_input.value())

        if supercom==[]:
            print("최소 1개의 IP가 입력되어야 합니다.")
            return
        else: 
            self.main_window.IP_ADDRESS=supercom
            self.main_window.WDIR= Analysis_setting(self.result_folder_input.text())



        self.main_window.ANALYSIS_TARGET = self.analysis_target_combo.currentText()  # 선택된 해석 대상 가져오기
        self.main_window.rpm4fl = self.rpm4fl_input.text()

        if not self.result_folder_input.text() or not self.uiwang_ip_input.text():
            print("해석 결과 폴더와 의왕 서버 IP를 입력해주세요")
            return
    
        # 모든 페이지의 테이블 업데이트
        if 'Screening' in self.main_window.pages:
            self.main_window.pages['Screening'].refresh_table()
        if 'AMR' in self.main_window.pages:
            self.main_window.pages['AMR'].refresh_table()
    def on_confirm_design_variables2(self):  # Load 용 확정 함수
        """설계변수 확정 버튼 클릭 시 호출"""
        # 선택된 설계 변수 정보 추출
        self.main_window.DV = []
        for row in range(self.table.rowCount()):
            combo_box = self.table.cellWidget(row, 4)
            if isinstance(combo_box, QComboBox) and combo_box.currentText() == '선택':
                try:
                    dv_item = {
                        'NAME': self.table.item(row, 0).text(),
                        'LV': float(self.table.item(row, 1).text()),
                        'UV': float(self.table.item(row, 2).text()),
                        'UNIT': self.table.item(row, 3).text()
                    }
                    self.main_window.DV.append(dv_item)
                except (ValueError, AttributeError):
                    print(f"설계 변수 정보 추출 중 오류 발생: 행 {row+1}의 데이터가 올바르지 않습니다.")
                    return
        
        # 선택된 출력 변수 정보 추출
        self.main_window.OV = []
        for row in range(self.output_table.rowCount()):
            combo_box = self.output_table.cellWidget(row, 2)
            if isinstance(combo_box, QComboBox) and combo_box.currentText() == '선택':
                try:
                    ov_item = {
                        'NAME': self.output_table.item(row, 0).text(),
                        'TARGET_ERROR': float(self.output_table.item(row, 1).text())
                    }
                    self.main_window.OV.append(ov_item)
                except (ValueError, AttributeError):
                    pass
        # 슈퍼컴 서버 정보 기록 
        supercom = []
        supercom.extend([self.uiwang_ip_input.text()] * self.uiwang_node_input.value())
        supercom.extend([self.gwangju_ip_input.text()] * self.gwangju_node_input.value())

        if supercom==[]:
            print("최소 1개의 IP가 입력되어야 합니다.")
            return
        else: 
            self.main_window.IP_ADDRESS=supercom
            self.main_window.WDIR=os.path.join(os.path.dirname(self.result_folder_input.text()), 'task')
            



        self.main_window.ANALYSIS_TARGET = self.analysis_target_combo.currentText()  # 선택된 해석 대상 가져오기
        self.main_window.rpm4fl = self.rpm4fl_input.text()

        if not self.result_folder_input.text() or not self.uiwang_ip_input.text():
            print("해석 결과 폴더와 의왕 서버 IP를 입력해주세요")
            return
    
        # 모든 페이지의 테이블 업데이트
        if 'Screening' in self.main_window.pages:
            self.main_window.pages['Screening'].refresh_table()
        if 'AMR' in self.main_window.pages:
            self.main_window.pages['AMR'].refresh_table()

    def on_browse_folder(self):
        """폴더 탐색 버튼 클릭 시 호출"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            '해석 결과 폴더 선택',
            '',
            QFileDialog.Option.ShowDirsOnly
        )
        if folder_path:
            self.result_folder_input.setText(folder_path)
    
    def on_save(self):
        """프로젝트 저장"""
        create_save(self.main_window)
    
    def on_load(self):
        """프로젝트 불러오기"""
        create_load(self.main_window)


