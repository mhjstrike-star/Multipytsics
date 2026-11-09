import sys
import os

try:
    from . import run_analysis
except ImportError:
    try:
        import run_analysis
    except ImportError:
        run_analysis = None

try:
    from . import controller
except ImportError:
    try:
        import controller
    except ImportError:
        controller = None

import asyncio
import logging
import os
import re
import time
import shutil
import csv

class solving:
 
    async def main (self, opath, rpm4fl, ip, DVname,x,Yname,f,Unit ,what,gen):
        '''AMR 실행 함수 (비동기)
        nx: 설계 변수 개수
        nobj: 목적함수 개수
        ncon: 제약조건 개수
        xl: 설계 변수 하한값 리스트
        xu: 설계 변수 상한값 리스트
        size_limit: 최대 실험점 개수
        accuracy_limit: 목표 오차율 리스트
        cpath: AMR 결과 저장 경로
        opath: 작업 디렉토리 경로
        rpm4fl: rpm4fl 값
        ip: IP 주소
        what: 분석 대상
        gen: 현재 세대 번호
        '''
        base_folder_path = os.path.dirname(opath).replace("\\", "/")
        runcount_file = os.path.join(base_folder_path, 'task', 'runcount.txt')
        if os.path.exists(runcount_file):
                        with open(runcount_file, 'r', encoding='utf-8') as rfile:
                            current_count = int(rfile.read().strip())
        else:
            current_count = 0
        # 로깅 설정
        log_file = os.path.join(os.path.dirname(opath), 'solving.log')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()  # 콘솔에도 출력
            ]
        )
        logger = logging.getLogger(__name__)
        logger.info(f'Solving main 함수 시작')
        logger.info(f'Parameters: opath={opath}, rpm4fl={rpm4fl}, ip={ip}, DVname={DVname}, gen={gen}')
        
        base_resultpath = f'{base_folder_path}__result'
        
        # f의 형태 확인: (npt, nf)로 reshape된 형태
        npt = len(x)
        nf = len(Yname) // npt if npt > 0 else 0
        logging.info(f'Total rows: {npt}, f shape: ({npt}, {nf})')
        
        # 4개의 워커가 각각 다른 폴더에서 담당 row들을 순차적으로 처리
        # 예: Worker 0 → row 0,4,8,... → folder_path_0, Worker 1 → row 1,5,9,... → folder_path_1
        tasks = [
            self._worker(worker_id, x, base_folder_path, DVname,Yname, Unit, rpm4fl, ip,what,current_count,gen)
            for worker_id in range(len(ip))
        ]
        
        worker_results_list = await asyncio.gather(*tasks)
        
        # 모든 워커의 결과를 수집하고 정렬
        all_results = {}    
        for worker_results in worker_results_list:
            all_results.update(worker_results)
        
        # indices 순서대로 정렬하여 f 배열에 업데이트
        sorted_indices = sorted(all_results.keys())
        
        # Restart.csv를 sorted_indices 순서대로 append 방식으로 작성 (파일 없을 때만 새로 생성)
        csv_path2 = f'{base_folder_path}/task/AMR_Result/Restart.csv'
        os.makedirs(os.path.dirname(csv_path2), exist_ok=True)
        
        # 파일이 없을 때만 새로 생성, 있으면 append 모드
        file_mode = 'w' if not os.path.exists(csv_path2) else 'a'
        
        try:
            max_retries = 45
            retry_count = 0
            while retry_count < max_retries:
                try:
                    with open(csv_path2, file_mode, encoding='utf-8', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        for orig_idx in sorted_indices:
                            row, row_f = all_results[orig_idx]  # (x, f) 튜플 unpacking
                            writer.writerow([*row, *row_f])
                    mode_desc = '새로 생성' if file_mode == 'w' else 'append'
                    logging.info(f'Restart.csv {mode_desc}: 순서대로 {len(sorted_indices)}개 행 추가')
                    break
                except (IOError, OSError) as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        logging.warning(f'Restart CSV 파일 작성 실패 (시도 {retry_count}/{max_retries}): {e}')
                        await asyncio.sleep(3)
                    else:
                        logging.error(f'Restart CSV 파일 작성 실패 (최대 재시도 횟수 초과): {e}')
                        raise
        except Exception as e:
            logging.error(f'Restart.csv 작성 중 오류: {e}')
        
        # indices 순서대로 정렬하여 f 배열에 업데이트
        
        # base_folder_path/task/runcount.txt 파일 읽고 업데이트
        
        try:
            
            new_count = current_count + len(x)
            
            os.makedirs(os.path.dirname(runcount_file), exist_ok=True)
            with open(runcount_file, 'w', encoding='utf-8') as wfile:
                wfile.write(str(new_count))
            
            logging.info(f'runcount.txt 업데이트: {current_count} + {len(x)} = {new_count}')
        except Exception as e:
            logging.error(f'runcount.txt 업데이트 중 오류: {e}')
        
        for new_idx, orig_idx in enumerate(sorted_indices):
            _, f_values = all_results[orig_idx]  # (x, f) 튜플에서 f만 추출
            f[new_idx] = f_values
        
        logging.info(f'모든 워커 완료 | 처리된 row: {sorted_indices}')

    async def log_result(self, base_folder_path, Yname, DVname, x, run_result, idx,NG,gen):
        csv_path = f'{base_folder_path}/task/AMR_Result/progress.csv'
        csv_path2 = f'{base_folder_path}/task/AMR_Result/Restart.csv'
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        
        # 헤더 생성 (파일이 없을 때만)
        file_exists = os.path.exists(csv_path)
        if not file_exists:
            header = ['index'] + list(DVname) + list(Yname) + ['OKNG', 'gen']
            try:
                with open(csv_path, 'w', encoding='utf-8', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(header)
                logging.info(f'CSV 파일 생성 완료: {csv_path}')
            except Exception as e:
                logging.error(f'CSV 헤더 작성 중 오류: {e}')
                raise
        
        # 데이터 행 작성 (재시도 로직 포함)
        max_retries = 45
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                with open(csv_path, 'a', encoding='utf-8', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow([idx, *x, *run_result, NG, gen])
                logging.info(f'CSV에 데이터 추가: idx={idx}')
                break
            except (IOError, OSError) as e:
                retry_count += 1
                if retry_count < max_retries:
                    logging.warning(f'CSV 파일 접근 실패 (시도 {retry_count}/{max_retries}): {e}')
                    await asyncio.sleep(3)
                else:
                    logging.error(f'CSV 파일 접근 실패 (최대 재시도 횟수 초과): {e}')
                    raise
        
        # csv_path2에 헤더 없이 [*x, *run_result] 기록 (재시도 로직)
        # → main()에서 sorted_indices 순서로 한 번에 작성하므로 여기서는 작성하지 않음
        # retry_count = 0
        # while retry_count < max_retries:
        #     try:
        #         with open(csv_path2, 'a', encoding='utf-8', newline='') as csvfile:
        #             writer = csv.writer(csvfile)
        #             writer.writerow([*x, *run_result])
        #         logging.info(f'Restart CSV에 데이터 추가: idx={idx}')
        #         break
        #     except (IOError, OSError) as e:
        #         retry_count += 1
        #         if retry_count < max_retries:
        #             logging.warning(f'Restart CSV 파일 접근 실패 (시도 {retry_count}/{max_retries}): {e}')
        #             await asyncio.sleep(3)
        #         else:
        #             logging.error(f'Restart CSV 파일 접근 실패 (최대 재시도 횟수 초과): {e}')
        #             raise
    async def check(self, path, flag):
        '''progress.txt 파일을 5초마다 읽고 step 완료 여부 확인 (비동기)
        path: 모니터링할 경로 (progress.txt가 있는 디렉토리)
        flag: 'mechanical' 또는 'electrical' 등의 분석 대상 구분
        
        조건:
        - 'step3 is finished'가 있으면 리턴
        - 'step4 is finished'가 있으면 flag가 'mechanical'일 때만 리턴
        '''
        progress_file = os.path.join(path, 'geom1', 'progress.txt')
        
        while True:
            try:
                if os.path.exists(progress_file):
                    content = None
                    # UTF-8과 ANSI(cp949) 인코딩 모두 지원
                    for encoding in ['utf-8', 'cp949', 'latin-1']:
                        try:
                            with open(progress_file, 'r', encoding=encoding) as f:
                                content = f.read()
                            break  # 성공하면 루프 탈출
                        except (UnicodeDecodeError, LookupError):
                            continue
                    
                    if content is None:
                        logging.warning(f'progress.txt를 읽을 수 없습니다: {progress_file}')
                        await asyncio.sleep(5)
                        continue
                    
                    # 'step3 is finished' 확인
                    if 'step3 is finished' in content and flag == 'Maxwell':
                        logging.info(f'step3 is finished 감지됨 (flag: {flag})')
                        return
                    elif 'step4 is finished' in content and flag == 'Mechanical':
                    # 'step4 is finished' 확인 (flag가 mechanical일 때만)
                        logging.info(f'step4 is finished 감지됨 (flag: {flag})')
                        return
                    elif 'step4 is finished' and 'step3 is finished' in content and flag == 'All':
                        logging.info(f'step3 & step4 is finished 감지됨 (flag: {flag})')
                        return
                
                # 5초 대기 (비동기)
                await asyncio.sleep(5)
                
            except Exception as e:
                logging.error(f'progress.txt 읽기 중 오류: {e}')
                await asyncio.sleep(5)

    async def _worker(self, worker_id, all_rows, base_folder_path, DVname, Yname, Unit, rpm4fl, ip, what, runcount, gen):
        '''각 워커가 자신의 폴더에서 담당 row들을 순차적으로 처리
        worker_id: 워커 ID (0~3)
        all_rows: 모든 row 리스트 (원본 indices)
        base_folder_path: 기본 폴더 경로 (예: D:/work/motor_name_1)
        nf: 각 row당 output 개수
        반환값: {row_idx: f_values_array} dict
        '''
        # 이 워커가 담당할 row indices 계산 (round-robin 방식)
        # worker 0: rows 0, 4, 8, ...
        # worker 1: rows 1, 5, 9, ...
        # worker 2: rows 2, 6, 10, ...
        # worker 3: rows 3, 7, 11, ...
        row_indices = list(range(worker_id, len(all_rows), len(ip)))
        
        # 이 워커만의 전용 폴더 경로

        
        # 이 워커의 결과 저장소: {row_idx: f_values}
        worker_results = {}
        
        try:
            for row_idx in row_indices:
                logging.info(f'[Worker {worker_id}] 시작 | 폴더: {base_folder_path} | 담당 row indices: {row_indices}')
                worker_folder_path = f"{base_folder_path}/task/{row_idx+runcount}"
                worker_resultpath = f"{worker_folder_path}__result"
                base_file_path= f"{base_folder_path}/task/base"
                
                # worker_folder_path와 worker_resultpath 폴더 생성 (없으면)
                
                if os.path.exists(worker_folder_path):
                    shutil.rmtree(worker_folder_path)
                os.makedirs(worker_folder_path, exist_ok=True)
                if os.path.exists(worker_resultpath):
                    shutil.rmtree(worker_resultpath)
                os.makedirs(worker_resultpath, exist_ok=True)
            
                
                logging.info(f'[Worker {worker_id}] {worker_folder_path} 폴더 생성 완료')
                logging.info(f'[Worker {worker_id}] {worker_resultpath} 폴더 생성 완료')
                
                # base_file_path 폴더 내의 모든 파일과 폴더를 worker_folder_path로 복사
                if os.path.exists(base_file_path):
                    for file_name in os.listdir(base_file_path):
                        src_file = os.path.join(base_file_path, file_name)
                        dst_file = os.path.join(worker_folder_path, file_name)
                        
                        if os.path.isdir(src_file):
                            # 폴더인 경우 재귀적으로 복사
                            shutil.copytree(src_file, dst_file, dirs_exist_ok=True)
                            logging.info(f'[Worker {worker_id}] 폴더 복사: {src_file} -> {dst_file}')
                        else:
                            # 파일인 경우 복사
                            shutil.copy2(src_file, dst_file)
                            logging.info(f'[Worker {worker_id}] 파일 복사: {src_file} -> {dst_file}')
                else:
                    logging.warning(f'[Worker {worker_id}] base_file_path 폴더를 찾을 수 없습니다: {base_file_path}')

                
                row = all_rows[row_idx]
                logging.info(f'[Worker {worker_id}] Row {row_idx} 처리 시작')
                
                # 각 row마다 고유한 temp instance 생성
                self.Input_edit(DV=DVname, path=worker_resultpath, x=row, Unit=Unit)
                
                # worker_resultpath/geom1 폴더 삭제
                try: 
                    geom_path = f'{worker_resultpath}/geom1'
                    if os.path.exists(geom_path):
                        shutil.rmtree(geom_path)
                        logging.info(f'[Worker {worker_id}] {geom_path} 폴더 삭제 완료')
                except Exception as e:
                    logging.error(f'[Worker {worker_id}] {geom_path} 폴더 삭제 중 오류: {e}')

                try: 
                    temp = run_analysis.AutoCal(worker_folder_path)
                    temp.get_X()
                    temp.cal_response(f'{worker_resultpath}/geom1.txt', rpm4FL=rpm4fl, what=what, ip=ip[worker_id])
                except Exception as e:
                    logging.error(f"[Worker {worker_id}] Row {row_idx} 처리 중 오류 발생: {e}")
                # controller 및 기타 변수는 외부에서 제공받아야 함
                logging.info(f'[IP: {ip[worker_id]}] What {what} path {worker_resultpath} Analysis Start')
                
                await self.check(worker_resultpath, what)  # 이 폴더에서 완료 대기
                
                # 이 row의 f 값 저장 (x와 row_f 모두 저장)
                row_f = [0.0] * len(Yname)
                NG=''
                NG=await self.output_read(f'{worker_resultpath}/geom1/result.csv',NG=NG, DV=DVname, Yname=Yname, O=row_f)
                await self.log_result(base_folder_path, Yname, DVname, row, row_f, row_idx+runcount,NG, gen)  # CSV에 기록
                worker_results[row_idx] = (row, row_f)  # (design vars, output values) 튜플로 저장
                 
                
                logging.info(f'[Worker {worker_id}] Row {row_idx} 완료 | f값: {row_f}')
                
        except Exception as e:
            logging.error(f'[Worker {worker_id}] 처리 중 오류: {e}')
        
        logging.info(f'[Worker {worker_id}] 모든 row 처리 완료 | 수집된 results: {list(worker_results.keys())}')
        return worker_results


    def Input_edit(self, DV, path,x,Unit) :  # path : Result Path

        names=DV
        units=Unit

        n = '\t'.join(names)
        paired_items = zip(x, units)
        combined_strings = [str(dv) + str(unit) for dv, unit in paired_items]
        final_string = '\t'.join(combined_strings)

        with open(f'{path}/geom1.txt', 'w', encoding='utf-8') as f:
            f.write(n + '\n')
            f.write(final_string )

    async def output_read(self, path,NG, DV, Yname, O) :
        import time
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            number_list = []
            
            # 파일 읽기
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) < 2:
                    return
                
                # 첫 번째 행: 헤더
                header_line = lines[0].strip()
                header_items = [item.strip() for item in header_line.split(',')]
                
                # 두 번째 행: 데이터
                data_line = lines[1].strip()
                data_items = [item.strip() for item in data_line.split(',')]

            if not data_line:
                return
            
            number_pattern = re.compile(r"[-+]?([0-9]*\.[0-9]+|[0-9]+)")
            
            # Yname의 각 항목에 대해 헤더에서 인덱스를 찾고 데이터 추출
            for yname in Yname:
                try:
                    col_idx = header_items.index(yname)
                    if col_idx < len(data_items):
                        item = data_items[col_idx]
                        # 공백 또는 NAN 체크
                        if not item or item.lower() == 'nan':
                            number_list.append(100000)
                            logging.error(f"Warning: '{yname}'의 값이 NAN입니다. 100000으로 대체합니다.")
                        else:
                            match = number_pattern.match(item.strip())
                            if match:
                                number_list.append(float(match.group(0)))
                            else:
                                # 숫자를 찾을 수 없으면 100000
                                number_list.append(100000)
                                logging.error(f"Warning: '{yname}'의 값이 숫자가 아닙니다. 100000으로 대체합니다.")
                    else:
                        number_list.append(100000)
                        logging.error(f"Warning: '{yname}'의 값이 존재하지 않습니다. 100000으로 대체합니다.")
                except ValueError:
                    # 헤더에서 항목을 찾지 못함
                    number_list.append(100000)
                    logging.error(f"Warning: '{yname}'의 값이 헤더에 없습니다. 100000으로 대체합니다.")
                
                try: 
                    col_idx = header_items.index('OKNG')
                    NG = data_items[col_idx]
                except:
                    NG = 'NG'
            
            # 100000과 100000이 아닌 값이 모두 존재하는지 확인
            has_100000 = any(val == 100000 for val in number_list)
            has_other = any(val != 100000 for val in number_list)
            
            if has_100000 and has_other:
                # 재시도 조건 만족: 100000과 다른 값이 모두 존재
                retry_count += 1
                if retry_count < max_retries:
                    logging.error(f"불완전한 데이터 감지 (100000과 실제값 혼재). {retry_count}회차 재시도 (3초 대기)...")
                    await asyncio.sleep(3)
                    continue
                else:
                    logging.error(f"최대 재시도 횟수({max_retries}) 초과. 현재 데이터로 진행합니다.")
            
            # 성공 또는 최대 재시도 초과: 데이터 저장
            for ind, number in enumerate(number_list):
                O[ind] = number
            break

        return NG


if __name__ == '__main__':
	
    dir_ip          = 'D:\\python_dir\\_ANSYS_AUTOCAL\\ipdata_lss'
    supercom_input  = {'10.98.40.101':{'cnt':3,'loc':'pj'}, '10.14.84.229':{'cnt':1,'loc':'gj'}}
    rpm4FL          = 100
    what            = 'all'
    
    # Test data - 2D matrix and variables
    import numpy as np
    test_matrix = np.array([
        [1.0, 2.5, 3.7, 4.2],
        [5.1, 6.8, 7.3, 8.9],
        [9.2, 10.5, 11.1, 12.6],
        [13.4, 14.8, 15.2, 16.9]
    ])
    
    test_opath = 'D:\\work\\2025_현대multi-physics\\SW\\output_submain'
    test_rpm4fl = 1500
    test_ip = '10.98.40.101'
    test_dvname = ['Param1', 'Param2', 'Param3', 'Param4']
    test_x = np.array([0.2, 0.5, 0.8, 0.3])  # Design variables
    test_f = np.array([45.2, 32.1, 58.9])     # Objective functions
    test_unit = ['mm', 'rpm', 'N', 'C']       # Units

    test_path ='C:\\Users\\m8909\\OneDrive - PIDOTECH\\바탕 화면\\result.csv'
    test_dvname=['Param1', 'Param2', 'Param3', 'Param4']
    O=[]
    test = solving()
    test.output_read(test_path,test_dvname,['Maximum Principal Stress'],O)
   


 