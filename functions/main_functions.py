"""
Main Page Functions
메인 페이지의 기능을 담당하는 모듈
"""
import os
import shutil
import json
from PySide6.QtWidgets import QFileDialog, QComboBox, QLineEdit, QTableWidgetItem


def load_IV_list():
    """
    all_ava_X.txt 파일을 읽어서 NAME, UNIT, Value를 포함한 딕셔너리 리스트 반환
    
    Returns:
        list: 각 항목이 {'NAME': str, 'UNIT': str, 'Value': float} 형식의 딕셔너리 리스트
    """
    file_path = os.path.join(os.path.dirname(__file__), '..', 'ANALYSIS_DATA', 'all_ava_X.txt')
    
    iv_list = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:  # 빈 줄 무시
                    continue
                
                # 탭으로 구분된 데이터 파싱
                parts = line.split('\t')
                
                if len(parts) >= 2:
                    name = parts[0].strip()
                    try:
                        value = float(parts[1].strip())
                    except ValueError:
                        continue
                    
                    # UNIT은 3번째 요소, 없으면 빈 문자열
                    unit = parts[2].strip() if len(parts) >= 3 else ''
                    
                    iv_list.append({
                        'NAME': name,
                        'UNIT': unit,
                        'Value': value
                    })
    
    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {file_path}")
        return []
    except Exception as e:
        print(f"파일 읽기 중 오류 발생: {e}")
        return []
    
    return iv_list


def load_OV_list():
    """
    all_ava_y.txt 파일을 읽어서 NAME, TARGET_ERROR를 포함한 딕셔너리 리스트 반환
    
    Returns:
        list: 각 항목이 {'NAME': str, 'TARGET_ERROR': str} 형식의 딕셔너리 리스트
    """
    file_path = os.path.join(os.path.dirname(__file__), '..', 'ANALYSIS_DATA', 'all_ava_y.txt')
    
    ov_list = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:  # 빈 줄 무시
                    continue
                
                # 탭으로 구분된 데이터 파싱
                parts = line.split('\t')
                
                if len(parts) >= 1:
                    name = parts[0].strip()
                    
                    # TARGET_ERROR는 2번째 요소, 없으면 빈 문자열
                    target_error = 5
                    
                    ov_list.append({
                        'NAME': name,
                        'TARGET_ERROR': target_error
                    })
    
    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {file_path}")
        return []
    except Exception as e:
        print(f"파일 읽기 중 오류 발생: {e}")
        return []
    
    return ov_list





def process_input(input_value):
    """
    입력값 처리
    
    Args:
        input_value (str): 사용자 입력값
    
    Returns:
        str: 처리 결과 메시지
    """
    if not input_value or input_value.strip() == '':
        return "오류: 입력값이 비어있습니다"
    return f"입력값 '{input_value}'이(가) 성공적으로 처리되었습니다"


def generate_table_data(row_count):
    """
    테이블 데이터 생성
    
    Args:
        row_count (int): 행 개수
    
    Returns:
        list: 테이블 데이터
    """
    data = []
    for i in range(row_count):
        row = {
            'parameter': f'파라미터_{i+1}',
            'value1': 10 * (i + 1),
            'value2': 20 * (i + 1),
            'value3': 30 * (i + 1),
            'status': '활성'
        }
        data.append(row)
    return data


def validate_table_data(table_data):
    """
    테이블 데이터 유효성 검사
    
    Args:
        table_data (list): 테이블 데이터
    
    Returns:
        tuple: (is_valid, message)
    """
    if not table_data:
        return False, "테이블에 데이터가 없습니다"
    
    if len(table_data) > 100:
        return False, "테이블 행의 개수가 너무 많습니다 (최대 100)"
    
    return True, "데이터가 유효합니다"

def Analysis_setting(dir):
    """
    해석 폴더 전달 후 Parallel 환경 구축을 위한 폴더 생성 및 파일 복사를 수행
    """
    task_dir=os.path.join(os.path.dirname(dir),'task')  # Task 폴더 없을 시 생성 
    amr_dir = os.path.join(task_dir, 'AMR_Result')  # AMR 폴더 없을 시 생성
    
    # task_dir이 존재하면, AMR_Result만 남기고 나머지는 삭제
    # if os.path.exists(task_dir):
    #     # for item in os.listdir(task_dir):
    #     #     item_path = os.path.join(task_dir, item)
    #     #     # AMR_Result는 건너뛰고 나머지만 삭제
    #     #     if item != 'AMR_Result':
    #     #         if os.path.isdir(item_path):
    #     #             shutil.rmtree(item_path)
    #     #         else:
    #     #             os.remove(item_path)
    #     pass
    # else:
    #     os.makedirs(task_dir, exist_ok=True)
    
    base_dir = os.path.join(task_dir, 'base')
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
    os.makedirs(base_dir)
    

    
    try:
        for item in os.listdir(dir):
            src_path = os.path.join(dir, item)
            dst_path = os.path.join(os.path.join(task_dir,'base'), item)
            
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
            else:
                shutil.copy2(src_path, dst_path)
    except Exception:
        pass
    return task_dir


def create_save(main_window):
    """프로젝트 저장 함수 - UI 데이터를 JSON으로 저장"""
    # 파일 저장 다이얼로그
    file_path, _ = QFileDialog.getSaveFileName(
        main_window,
        '프로젝트 저장',
        '',
        'JSON Files (*.json);;All Files (*)'
    )
    
    if not file_path:
        return
    
    # 저장할 데이터 구조
    project_data = {
        'main': {},
        'screening': {},
        'amr': {},
        'do': {}
    }
    
    # Main 페이지 데이터 추출
    if 'Main' in main_window.pages:
        page_main = main_window.pages['Main']
        project_data['main'] = _extract_main_data(page_main)
    
    # Screening 페이지 데이터 추출
    if 'Screening' in main_window.pages:
        page_screening = main_window.pages['Screening']
        project_data['screening'] = _extract_screening_data(page_screening)
    
    # AMR 페이지 데이터 추출
    if 'AMR' in main_window.pages:
        page_amr = main_window.pages['AMR']
        project_data['amr'] = _extract_amr_data(page_amr)
    
    # DO 페이지 데이터 추출
    if 'DO' in main_window.pages:
        page_do = main_window.pages['DO']
        project_data['do'] = _extract_do_data(page_do)
    
    # JSON 파일로 저장
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, indent=4, ensure_ascii=False)
        print(f"프로젝트가 저장되었습니다: {file_path}")
    except Exception as e:
        print(f"프로젝트 저장 중 오류 발생: {e}")


def create_load(main_window):
    """프로젝트 불러오기 함수 - JSON 파일에서 데이터를 읽어 UI에 적용"""
    # 파일 열기 다이얼로그
    file_path, _ = QFileDialog.getOpenFileName(
        main_window,
        '프로젝트 불러오기',
        '',
        'JSON Files (*.json);;All Files (*)'
    )
    
    if not file_path:
        return
    
    # JSON 파일 읽기
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
    except Exception as e:
        print(f"파일 읽기 중 오류 발생: {e}")
        return
    
    # 파일 서식 검증
    if not _validate_project_file(project_data):
        print("잘못된 Save 파일입니다. 파일 형식이 일치하지 않습니다.")
        return
    
    # Main 페이지 데이터 적용
    if 'Main' in main_window.pages and project_data.get('main'):
        page_main = main_window.pages['Main']
        _load_main_data(page_main, project_data['main'])
        
        # on_confirm_design_variables2 실행 (AMR이나 Screening에 데이터가 있으면)
        if project_data.get('amr') or project_data.get('screening'):
            page_main.on_confirm_design_variables2()
    
    # Screening 페이지 데이터 적용
    if 'Screening' in main_window.pages and project_data.get('screening'):
        page_screening = main_window.pages['Screening']
        _load_screening_data(page_screening, project_data['screening'])
    
    # AMR 페이지 데이터 적용
    if 'AMR' in main_window.pages and project_data.get('amr'):
        page_amr = main_window.pages['AMR']
        _load_amr_data(page_amr, project_data['amr'])
    
    # DO 페이지 데이터 적용
    if 'DO' in main_window.pages and project_data.get('do'):
        page_do = main_window.pages['DO']
        _load_do_data(page_do, project_data['do'])
    
    print(f"프로젝트가 불러와졌습니다: {file_path}")


def _validate_project_file(project_data):
    """프로젝트 파일의 서식 유효성 검증"""
    # 필수 섹션 확인
    required_sections = ['main', 'screening', 'amr', 'do']
    for section in required_sections:
        if section not in project_data:
            return False
    
    # Main 섹션 필수 필드 확인
    main_data = project_data.get('main', {})
    required_main_fields = ['design_variables', 'output_variables', 'result_folder', 
                            'paju_ip', 'paju_nodes', 'gwangju_ip', 'gwangju_nodes', 
                            'rpm4fl', 'analysis_target']
    for field in required_main_fields:
        if field not in main_data:
            return False
    
    return True


def _load_main_data(page_main, main_data):
    """Main 페이지에 데이터 적용"""
    # 설계변수 테이블 업데이트
    design_vars = main_data.get('design_variables', [])
    if design_vars:
        page_main.table.setRowCount(len(design_vars))
        for row, dv in enumerate(design_vars):
            page_main.table.setRowHeight(row, 35)
            
            # 0열: name
            page_main.table.setItem(row, 0, QTableWidgetItem(dv.get('name', '')))
            # 1열: lower_limit
            page_main.table.setItem(row, 1, QTableWidgetItem(dv.get('lower_limit', '')))
            # 2열: upper_limit
            page_main.table.setItem(row, 2, QTableWidgetItem(dv.get('upper_limit', '')))
            # 3열: unit
            page_main.table.setItem(row, 3, QTableWidgetItem(dv.get('unit', '')))
            # 4열: selected (ComboBox)
            combo_box = QComboBox()
            combo_box.addItems(['선택', '선택안함'])
            combo_box.setCurrentText(dv.get('selected', '선택안함'))
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
            page_main.table.setCellWidget(row, 4, combo_box)
    
    # 출력변수 테이블 업데이트
    output_vars = main_data.get('output_variables', [])
    if output_vars:
        page_main.output_table.setRowCount(len(output_vars))
        for row, ov in enumerate(output_vars):
            page_main.output_table.setRowHeight(row, 35)
            
            # 0열: name
            page_main.output_table.setItem(row, 0, QTableWidgetItem(ov.get('name', '')))
            # 1열: target_error
            page_main.output_table.setItem(row, 1, QTableWidgetItem(ov.get('target_error', '')))
            # 2열: selected (ComboBox)
            combo_box = QComboBox()
            combo_box.addItems(['선택', '선택안함'])
            combo_box.setCurrentText(ov.get('selected', '선택안함'))
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
            page_main.output_table.setCellWidget(row, 2, combo_box)
    
    # 텍스트 필드 복원
    page_main.result_folder_input.setText(main_data.get('result_folder', ''))
    page_main.uiwang_ip_input.setText(main_data.get('paju_ip', ''))
    page_main.uiwang_node_input.setValue(main_data.get('paju_nodes', 1))
    page_main.gwangju_ip_input.setText(main_data.get('gwangju_ip', ''))
    page_main.gwangju_node_input.setValue(main_data.get('gwangju_nodes', 1))
    page_main.rpm4fl_input.setText(main_data.get('rpm4fl', '100'))
    page_main.analysis_target_combo.setCurrentText(main_data.get('analysis_target', 'All'))


def _load_screening_data(page_screening, screening_data):
    """Screening 페이지에 데이터 적용"""
    # 설계변수 테이블 업데이트
    design_vars = screening_data.get('design_variables', [])
    if design_vars:
        page_screening.table.setRowCount(len(design_vars))
        for row, dv in enumerate(design_vars):
            page_screening.table.setRowHeight(row, 35)
            
            page_screening.table.setItem(row, 0, QTableWidgetItem(dv.get('name', '')))
            page_screening.table.setItem(row, 1, QTableWidgetItem(dv.get('lower_limit', '')))
            page_screening.table.setItem(row, 2, QTableWidgetItem(dv.get('upper_limit', '')))
            page_screening.table.setItem(row, 3, QTableWidgetItem(dv.get('unit', '')))
    
    # 출력변수 테이블 업데이트
    output_vars = screening_data.get('output_variables', [])
    if output_vars:
        page_screening.output_table.setRowCount(len(output_vars))
        for row, ov in enumerate(output_vars):
            page_screening.output_table.setRowHeight(row, 35)
            
            page_screening.output_table.setItem(row, 0, QTableWidgetItem(ov.get('name', '')))
            page_screening.output_table.setItem(row, 1, QTableWidgetItem(ov.get('target_error', '')))


def _load_amr_data(page_amr, amr_data):
    """AMR 페이지에 데이터 적용"""
    # 설계변수 테이블 업데이트
    design_vars = amr_data.get('design_variables', [])
    if design_vars:
        page_amr.table.setRowCount(len(design_vars))
        for row, dv in enumerate(design_vars):
            page_amr.table.setRowHeight(row, 35)
            
            page_amr.table.setItem(row, 0, QTableWidgetItem(dv.get('name', '')))
            page_amr.table.setItem(row, 1, QTableWidgetItem(dv.get('lower_limit', '')))
            page_amr.table.setItem(row, 2, QTableWidgetItem(dv.get('upper_limit', '')))
            page_amr.table.setItem(row, 3, QTableWidgetItem(dv.get('unit', '')))
    
    # 출력변수 테이블 업데이트
    output_vars = amr_data.get('output_variables', [])
    if output_vars:
        page_amr.output_table.setRowCount(len(output_vars))
        for row, ov in enumerate(output_vars):
            page_amr.output_table.setRowHeight(row, 35)
            
            page_amr.output_table.setItem(row, 0, QTableWidgetItem(ov.get('name', '')))
            page_amr.output_table.setItem(row, 1, QTableWidgetItem(ov.get('target_error', '')))
    
    # 파라미터 복원
    if amr_data.get('max_exp'):
        page_amr.max_exp_spinbox.setValue(amr_data.get('max_exp', 100))
    
    if amr_data.get('convergence'):
        page_amr.convergence_spinbox.setValue(amr_data.get('convergence', 10))
    
    # 작업 이어하기 경로 복원
    page_amr.info_path.setText(amr_data.get('info_path', ''))


def _load_do_data(page_do, do_data):
    """DO 페이지에 데이터 적용"""
    # 메타모델 경로 복원
    page_do.metamodel_path_input.setText(do_data.get('metamodel_path', ''))
    
    # 설계변수 테이블 업데이트
    design_vars = do_data.get('design_variables', [])
    if design_vars:
        page_do.table.setRowCount(len(design_vars))
        for row, dv in enumerate(design_vars):
            page_do.table.setRowHeight(row, 35)
            
            page_do.table.setItem(row, 0, QTableWidgetItem(dv.get('name', '')))
            page_do.table.setItem(row, 1, QTableWidgetItem(dv.get('lower_limit', '')))
            page_do.table.setItem(row, 2, QTableWidgetItem(dv.get('upper_limit', '')))
            page_do.table.setItem(row, 3, QTableWidgetItem(dv.get('unit', '')))
            page_do.table.setItem(row, 4, QTableWidgetItem(dv.get('discrete_set', '')))
    
    # 출력변수 테이블 업데이트
    output_vars = do_data.get('output_variables', [])
    if output_vars:
        page_do.output_table.setRowCount(len(output_vars))
        for row, ov in enumerate(output_vars):
            page_do.output_table.setRowHeight(row, 35)
            
            # 0열: name
            page_do.output_table.setItem(row, 0, QTableWidgetItem(ov.get('name', '')))
            
            # 1열: objective_type (ComboBox)
            combo_box = QComboBox()
            combo_box.addItems(['목적함수(최소화)', '목적함수(최대화)', '구속조건', '사용안함'])
            combo_box.setCurrentText(ov.get('objective_type', '사용안함'))
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
            page_do.output_table.setCellWidget(row, 1, combo_box)
            
            # 2열: lower_bound (QLineEdit)
            lower_input = QLineEdit()
            lower_input.setText(ov.get('lower_bound', ''))
            lower_input.setStyleSheet("""
                QLineEdit {
                    background-color: #3d3d3d;
                    color: #e0e0e0;
                    border: 1px solid #0d47a1;
                    padding: 2px;
                }
            """)
            page_do.output_table.setCellWidget(row, 2, lower_input)
            
            # 3열: upper_bound (QLineEdit)
            upper_input = QLineEdit()
            upper_input.setText(ov.get('upper_bound', ''))
            upper_input.setStyleSheet("""
                QLineEdit {
                    background-color: #3d3d3d;
                    color: #e0e0e0;
                    border: 1px solid #0d47a1;
                    padding: 2px;
                }
            """)
            page_do.output_table.setCellWidget(row, 3, upper_input)


def _extract_main_data(page_main):
    """Main 페이지 데이터 추출"""
    data = {
        'design_variables': [],
        'output_variables': [],
        'result_folder': '',
        'paju_ip': '',
        'paju_nodes': 0,
        'gwangju_ip': '',
        'gwangju_nodes': 0,
        'rpm4fl': '',
        'analysis_target': ''
    }
    
    # 입력변수 테이블 데이터 추출
    if hasattr(page_main, 'table'):
        for row in range(page_main.table.rowCount()):
            row_data = {
                'name': page_main.table.item(row, 0).text() if page_main.table.item(row, 0) else '',
                'lower_limit': page_main.table.item(row, 1).text() if page_main.table.item(row, 1) else '',
                'upper_limit': page_main.table.item(row, 2).text() if page_main.table.item(row, 2) else '',
                'unit': page_main.table.item(row, 3).text() if page_main.table.item(row, 3) else '',
                'selected': ''
            }
            
            combo_box = page_main.table.cellWidget(row, 4)
            if isinstance(combo_box, QComboBox):
                row_data['selected'] = combo_box.currentText()
            
            data['design_variables'].append(row_data)
    
    # 출력변수 테이블 데이터 추출
    if hasattr(page_main, 'output_table'):
        for row in range(page_main.output_table.rowCount()):
            row_data = {
                'name': page_main.output_table.item(row, 0).text() if page_main.output_table.item(row, 0) else '',
                'target_error': page_main.output_table.item(row, 1).text() if page_main.output_table.item(row, 1) else '',
                'selected': ''
            }
            
            combo_box = page_main.output_table.cellWidget(row, 2)
            if isinstance(combo_box, QComboBox):
                row_data['selected'] = combo_box.currentText()
            
            data['output_variables'].append(row_data)
    
    # 텍스트 필드 데이터 추출
    if hasattr(page_main, 'result_folder_input'):
        data['result_folder'] = page_main.result_folder_input.text()
    
    if hasattr(page_main, 'uiwang_ip_input'):
        data['paju_ip'] = page_main.uiwang_ip_input.text()
    
    if hasattr(page_main, 'uiwang_node_input'):
        data['paju_nodes'] = page_main.uiwang_node_input.value()
    
    if hasattr(page_main, 'gwangju_ip_input'):
        data['gwangju_ip'] = page_main.gwangju_ip_input.text()
    
    if hasattr(page_main, 'gwangju_node_input'):
        data['gwangju_nodes'] = page_main.gwangju_node_input.value()
    
    if hasattr(page_main, 'rpm4fl_input'):
        data['rpm4fl'] = page_main.rpm4fl_input.text()
    
    if hasattr(page_main, 'analysis_target_combo'):
        data['analysis_target'] = page_main.analysis_target_combo.currentText()
    
    return data


def _extract_screening_data(page_screening):
    """Screening 페이지 데이터 추출"""
    data = {
        'design_variables': [],
        'output_variables': []
    }
    
    # 입력변수 테이블 데이터 추출
    if hasattr(page_screening, 'table'):
        for row in range(page_screening.table.rowCount()):
            row_data = {
                'name': page_screening.table.item(row, 0).text() if page_screening.table.item(row, 0) else '',
                'lower_limit': page_screening.table.item(row, 1).text() if page_screening.table.item(row, 1) else '',
                'upper_limit': page_screening.table.item(row, 2).text() if page_screening.table.item(row, 2) else '',
                'unit': page_screening.table.item(row, 3).text() if page_screening.table.item(row, 3) else ''
            }
            data['design_variables'].append(row_data)
    
    # 출력변수 테이블 데이터 추출
    if hasattr(page_screening, 'output_table'):
        for row in range(page_screening.output_table.rowCount()):
            row_data = {
                'name': page_screening.output_table.item(row, 0).text() if page_screening.output_table.item(row, 0) else '',
                'target_error': page_screening.output_table.item(row, 1).text() if page_screening.output_table.item(row, 1) else ''
            }
            data['output_variables'].append(row_data)
    
    return data


def _extract_amr_data(page_amr):
    """AMR 페이지 데이터 추출"""
    data = {
        'design_variables': [],
        'output_variables': [],
        'max_exp': 0,
        'convergence': 0,
        'info_path': ''
    }
    
    # 입력변수 테이블 데이터 추출
    if hasattr(page_amr, 'table'):
        for row in range(page_amr.table.rowCount()):
            row_data = {
                'name': page_amr.table.item(row, 0).text() if page_amr.table.item(row, 0) else '',
                'lower_limit': page_amr.table.item(row, 1).text() if page_amr.table.item(row, 1) else '',
                'upper_limit': page_amr.table.item(row, 2).text() if page_amr.table.item(row, 2) else '',
                'unit': page_amr.table.item(row, 3).text() if page_amr.table.item(row, 3) else ''
            }
            data['design_variables'].append(row_data)
    
    # 출력변수 테이블 데이터 추출
    if hasattr(page_amr, 'output_table'):
        for row in range(page_amr.output_table.rowCount()):
            row_data = {
                'name': page_amr.output_table.item(row, 0).text() if page_amr.output_table.item(row, 0) else '',
                'target_error': page_amr.output_table.item(row, 1).text() if page_amr.output_table.item(row, 1) else ''
            }
            data['output_variables'].append(row_data)
    
    # 파라미터 추출
    if hasattr(page_amr, 'max_exp_spinbox'):
        data['max_exp'] = page_amr.max_exp_spinbox.value()
    
    if hasattr(page_amr, 'convergence_spinbox'):
        data['convergence'] = page_amr.convergence_spinbox.value()
    
    # 작업 이어하기 경로 추출
    if hasattr(page_amr, 'info_path'):
        data['info_path'] = page_amr.info_path.text()
    
    return data


def _extract_do_data(page_do):
    """DO 페이지 데이터 추출"""
    data = {
        'metamodel_path': '',
        'design_variables': [],
        'output_variables': []
    }
    
    # 메타모델 경로 추출
    if hasattr(page_do, 'metamodel_path_input'):
        data['metamodel_path'] = page_do.metamodel_path_input.text()
    
    # 입력변수 테이블 데이터 추출 (5열)
    if hasattr(page_do, 'table'):
        for row in range(page_do.table.rowCount()):
            row_data = {
                'name': page_do.table.item(row, 0).text() if page_do.table.item(row, 0) else '',
                'lower_limit': page_do.table.item(row, 1).text() if page_do.table.item(row, 1) else '',
                'upper_limit': page_do.table.item(row, 2).text() if page_do.table.item(row, 2) else '',
                'unit': page_do.table.item(row, 3).text() if page_do.table.item(row, 3) else '',
                'discrete_set': page_do.table.item(row, 4).text() if page_do.table.item(row, 4) else ''
            }
            data['design_variables'].append(row_data)
    
    # 출력변수 테이블 데이터 추출
    if hasattr(page_do, 'output_table'):
        for row in range(page_do.output_table.rowCount()):
            row_data = {
                'name': page_do.output_table.item(row, 0).text() if page_do.output_table.item(row, 0) else '',
                'objective_type': '',
                'lower_bound': '',
                'upper_bound': ''
            }
            
            # Column 1: 목적함수/구속조건 (ComboBox)
            combo_widget = page_do.output_table.cellWidget(row, 1)
            if isinstance(combo_widget, QComboBox):
                row_data['objective_type'] = combo_widget.currentText()
            
            # Column 2: 구속조건 하한값 (QLineEdit)
            lower_widget = page_do.output_table.cellWidget(row, 2)
            if isinstance(lower_widget, QLineEdit):
                row_data['lower_bound'] = lower_widget.text()
            
            # Column 3: 구속조건 상한값 (QLineEdit)
            upper_widget = page_do.output_table.cellWidget(row, 3)
            if isinstance(upper_widget, QLineEdit):
                row_data['upper_bound'] = upper_widget.text()
            
            data['output_variables'].append(row_data)
    
    return data
