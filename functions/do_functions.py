
import time
import numpy as np
import os
import glob
from IMM import MMIntegrator
import re

def obj(self,X):
    self.F=[]  # 초기화
    self.G=[]

    rcount=int(len(X)/self.ndv)
    x2d=X.reshape(rcount,self.ndv)
    G =[]
    O = []
    so= []  # sum of obj
    # 파일 종료
    

    for row in x2d :
        try:
            O,G=self.cal_objpy(row,O,G)
            
        except Exception as e:
            O.extend([100] * self.nobj)
            G.extend([200] * self.ncon)
            print(f"Error processing row {row}: {e}")
                
        self.calcount+=1
        elapsed_sec = time.time() - self.initialtime
        hours = int(elapsed_sec // 3600)
        minutes = int((elapsed_sec % 3600) // 60)
        seconds = int(elapsed_sec % 60)
        print(f'최적화 반복해석 {self.calcount} 회차 완료'
                f'소요시간: {hours:02d}:{minutes:02d}:{seconds:02d}')
        
            # if self.calcount>5 :
            #     self.open_workbook_safly()
            #     self.value_update()
            #     try:
            #         self.Engine.close()
            #     except Exception:
            #         pass
            #     try:
            #         del self.Engine
            #     except Exception:
            #         pass
            #     self.Engine = None
            #     self.Engine = Plogic.GSEP_Engine(wb=self.Dexcel)
            #     self.calcount=0
    self.G=np.array(G)
    self.F=np.array(O)
    return self.F

class DO:
    def __init__(self, DV_info, output_info,meta_path):
        self.ndv = len(DV_info)
        objcount= 0
        concount=0
        self.output_info = output_info
        for item in output_info:
            if item.get('objective_type') == '목적함수(최대화)' or item.get('objective_type') == '목적함수(최소화)':
                objcount += 1
            elif item.get('objective_type') == '구속조건':
                if item.get('lower_bound') != None and item.get('upper_bound') != None:
                    concount += 2    
                elif item.get('lower_bound') != None or item.get('upper_bound') != None:
                    concount += 1
                
        self.nobj = objcount
        self.ncon = concount
        self.DV_info = DV_info
        self.LB = [item.get('lv') for item in DV_info]  # 하한값 리스트
        self.UB = [item.get('uv') for item in DV_info]  # 상한값 리스트
        self.DisLvX=[]
        self.DisSetX=[]
        self._meta_layout_cache = {}
        for item in DV_info:
            if item.get('discrete_set') == '':
                self.DisLvX.append(0)
            else:
                self.DisLvX.append(len(item.get('discrete_set').split(',')))
                self.DisSetX.append(item.get('discrete_set').split(','))
        self.meta_path = meta_path


    def obj(self, X):
        F=[]  # 초기화
        G=[]  # 초기화
        rcount=int(len(X)/self.ndv)
        x2d=X.reshape(rcount,self.ndv)

        dvnames = [item.get('name') for item in self.DV_info]
        objnames = [item.get('name') for item in self.output_info if item.get('objective_type') in ['목적함수(최대화)', '목적함수(최소화)']]
        connames = [item.get('name') for item in self.output_info if item.get('objective_type') == '구속조건']
        outnames = [item.get('name') for item in self.output_info]
        temp=[]
        for row in x2d :
            result = self.mdet_run(self.meta_path, np.array(row), dvnames,objnames,connames,outnames)
            for idx, (key, data) in enumerate(result.items()): # data : metamodel output
                item = self.output_info[idx]   # item : output_info
                if item.get('objective_type') == '목적함수(최대화)':
                    temp.append(float(-1*data['value'][0]))
                elif item.get('objective_type') == '목적함수(최소화)':
                    temp.append(float(data['value'][0]))
                elif item.get('objective_type') == '구속조건':
                    if item.get('upper_bound') is not None:
                        G.append(float(data['value'][0]-item.get('upper_bound')))   
                    if item.get('lower_bound') is not None:
                        G.append(float(item.get('lower_bound')-data['value'][0]))
            F.append(sum(temp))
        self.F=np.array(F)
        self.G=np.array(G)
        
        return self.F

    def con(self, X):

        return self.G

    def mdet_run(self, address,allx,xname,objname,conname,outname):
        cache_key = os.path.normcase(os.path.abspath(address))
       
        layout = self._meta_layout_cache.get(cache_key)
        path_cfile=os.path.join(address,"AMR.LOG")
        best_model = []

        # AMR.LOG에서 best model 파싱
        if os.path.exists(path_cfile):
            with open(path_cfile, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 파일을 역순으로 탐색해서 가장 마지막 convergence_info 찾기
            for i in range(len(lines) - 1, -1, -1):
                line = lines[i].strip()
                
                if 'convergence_info' in line:
                    # convergence_info 라인에서 출력변수명들 추출
                    parts = line.split()
                    # convergence_info 이후의 값들이 출력변수명
                    conv_info_idx = None
                    for idx, part in enumerate(parts):
                        if 'convergence_info' in part:
                            conv_info_idx = idx
                            break
                    
                    if conv_info_idx is not None:
                        output_names = parts[conv_info_idx + 1:]
                    else:
                        output_names = []
                    
                    # 이 섹션에서 best model 라인 찾기
                    best_model_values = []
                    for j in range(i, min(i + 20, len(lines))):
                        section_line = lines[j].strip()
                        if section_line.startswith('best model'):
                            model_parts = section_line.split()
                            # 'best model' 이후의 값들이 각 출력변수의 best model
                            best_model_values = model_parts[2:]
                            break
                    
                    # 출력변수명과 best model 매핑
                    best_model_dict = {}
                    for idx, output_name in enumerate(output_names):
                        if idx < len(best_model_values):
                            best_model_dict[output_name] = best_model_values[idx]
                    
                    # objname 순서대로 best_model 리스트 구성
                    for output in outname:
                        if output in best_model_dict:
                            best_model.append(best_model_dict[output])
                        else:
                            best_model.append(None)
                    
                    break
                    

        moutput={}
        for idx, output in enumerate(outname):
            dir = os.path.join(address, "_metamodels", f'F{idx+1}_{best_model_dict[output]}')
            for dirpath, dirnames, filenames in os.walk(dir):
                for filename in filenames:
                    if filename.lower().endswith('.mt5'):
                        full_path = os.path.join(dirpath, filename)
            mmi = MMIntegrator()
            mmi.load(binpathname=full_path)
            fapp = mmi.predict(np.array(allx))
            moutput[idx] = {'name': outname[idx],'value':fapp}
            mmi=None  # mmi 초기화 
            
            
    

        return moutput

def meta_ParseV(metamodel_path):
    """
    메타모델 폴더에서 .IN 및 .OUT 파일을 찾아 변수명을 추출하는 함수
    195줄부터 AMR.LOG를 파싱하여 ndv와 vf를 추출
    
    Args:
        metamodel_path: 메타모델 폴더 경로
        page_do_instance: PageDO 클래스 인스턴스
    
    Returns:
        dv_list: INPUT 변수명 리스트
        out_list: OUTPUT 변수명 리스트
    """
    dv_list = []
    out_list = []
    ndv = None
    vf = None
    
    try:
        # AMR.LOG 파일에서 ndv와 vf 읽기
        amr_log_path = os.path.join(metamodel_path, 'AMR.LOG')
        if os.path.exists(amr_log_path):
            try:
                with open(amr_log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            except Exception as e:
                print(f"AMR.LOG 파일 읽기 중 오류 발생: {e}")
                return [], []

        # 195줄부터 시작 (인덱스 194부터)
    except Exception as e:
        
        return [], []
    for line in lines:
        
        
        if "Number of input variables" in line:
            parts = line.split(',')
            if len(parts) > 1:
                ndv = int(parts[1].strip())
        
        if "Number of output variables" in line:
            parts = line.split(',')
            if len(parts) > 1:
                vf = int(parts[1].strip())
        
        # 두 변수 모두 찾았으면 루프 종료
        if ndv is not None and vf is not None:
            break
    if ndv is None or vf is None:
        print("AMR.LOG 파일에서 입력 변수 개수 또는 출력 변수 개수를 찾을 수 없습니다.")
        return [], []

    for ind, line in enumerate(lines):
        pattern = r'\s*iteration:\s*(\d+)\s*/\s*train:'
        match = re.search(pattern, line)
        if match is not None:
            tline=lines[ind+2].split()
            dv_list = tline[1:ndv+1]
            out_list = tline[ndv+1:ndv+1+vf]

        
    return dv_list, out_list    
    



def AMR_ParseV(metamodel_path):
    """
    메타모델 폴더에서 .IN 및 .OUT 파일을 찾아 변수명을 추출하는 함수
    
    Args:
        metamodel_path: 메타모델 폴더 경로
        page_do_instance: PageDO 클래스 인스턴스
    
    Returns:
        dv_list: INPUT 변수명 리스트
        out_list: OUTPUT 변수명 리스트
    """
    dv_list = []
    out_list = []
    
    try:
        # .IN 파일 찾기
        in_files = glob.glob(os.path.join(metamodel_path, '*.in'))
        if in_files:
            in_file = in_files[0]  # 첫 번째 .IN 파일 사용
            print(f"INPUT 파일 발견: {in_file}")
            
            with open(in_file, 'r') as f:
                lines = f.readlines()
                # 2행부터 탐색 (인덱스 1부터)
                for i in range(1, len(lines)):
                    line = lines[i].strip()
                    if line == 'END' or not line:
                        break
                    # '변수명 = 값' 형식에서 변수명만 추출
                    if '=' in line:
                        var_name = line.split('=')[0].strip()
                        if var_name and var_name != '$NDV':
                            dv_list.append(var_name)
        
        # .OUT 파일 찾기
        out_files = glob.glob(os.path.join(metamodel_path, '*.out'))
        if out_files:
            out_file = out_files[0]  # 첫 번째 .OUT 파일 사용
            print(f"OUTPUT 파일 발견: {out_file}")
            
            with open(out_file, 'r') as f:
                lines = f.readlines()
                # 전체 파일 탐색
                for line in lines:
                    line = line.strip()
                    if line == 'END' or not line:
                        continue
                    # '변수명 = 값' 형식에서 변수명만 추출
                    if '=' in line:
                        var_name = line.split('=')[0].strip()
                        if var_name:
                            out_list.append(var_name)
        
        # 페이지 인스턴스에 저장
        print(f"INPUT 변수 개수: {len(dv_list)}")
        print(f"OUTPUT 변수 개수: {len(out_list)}")
        
        return dv_list, out_list
    
    except Exception as e:
        print(f"메타모델 로드 중 오류 발생: {e}")
        return [], []


if __name__ == '__main__':
    # 테스트용 메타모델 경로 설정
  

    
    test_metamodel_path = r"D:\\work\\2025_현대multi-physics\\testfolder\\task\\AMR_Result"
    
    # ParseV 함수 호출
    dv_list, out_list = meta_ParseV(test_metamodel_path)
    
    # 결과 출력
    print("INPUT 변수명 리스트:", dv_list)
    print("OUTPUT 변수명 리스트:", out_list)