from operator import index

import numpy as np
import os
from os import sys
import platform
import asyncio
import logging
import shutil
try: from . import run_analysis
except ImportError:
    try: import run_analysis
    except ImportError: run_analysis = None
try: from .solve import solving  # Main.py에서 import될 때
except ImportError: from solve import solving   # 이 파일을 직접 실행할 때
from AMR import *
from IMM import MMIntegrator
class communicator(object):
    def __init__(self, nx, nf,opath, rpm4fl, ip, DVname,Yname,Unit, what):
        self.nx = nx
        self.nf = nf  
        self.opath = opath
        self.rpm4fl = rpm4fl
        self.ip = ip
        self.DVname = DVname
        self.Yname=Yname
        self.Unit=Unit
        self._stop = False
        self.what=what
        self.generation=1
        # 로깅 설정
        log_file = os.path.join(opath, 'amrfunction.log')
        if os.path.exists(log_file):  # 로그파일 초기화
            os.remove(log_file)
        self.logger = logging.getLogger(f'communicator_{id(self)}')
        self.logger.setLevel(logging.INFO)
        
        # 기존 핸들러 제거 (중복 방지)
        self.logger.handlers = []
        
        # propagate 비활성화 - root logger로의 전파 방지
        self.logger.propagate = False
        
        # 파일 핸들러
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 포매터
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # 초기 로그 메시지
        self.logger.info('Logger initialized successfully')
        self.allrun= []
    
    def Analysis(self, x, f):
        try:
            npt = int(len(x)/self.nx) # Sampling 결과 32케이스 32x1 list  npt = 32/4(설계변수 개수)
            f = np.reshape(f, (npt,self.nf))    # Sampling 결과 32케이스 32x1 list -> 출력변수가 1개면 8x1     
            x = np.reshape(x, (npt,self.nx))    # 설계 변수 4개인 경우 8x4 2d np array  
            test=solving()
            asyncio.run(test.main(x=x, f=f, opath=self.opath, rpm4fl=float(self.rpm4fl),ip=self.ip, DVname=self.DVname, Yname=self.Yname, Unit=self.Unit,what=self.what,gen=self.generation))
            self.generation += 1   # 세대수 증가
            self.logger.info('Solving 완료')
            self.f = f.flatten()
            self.logger.info('Analysis 완료')

            

            self.allrun.extend([*xi, *fi] for xi, fi in zip(x, f))
            
                 
        except Exception as e:
            self.logger.error(f'Analysis 중 오류 발생: {e}', exc_info=True)
            print(f"Error during Analysis: {e}")
            return

    def Export(self, datainfo, modelinfo):  
        nx, nf, npt, xtrain, ftrain, xtest, ftest = datainfo[0], datainfo[1], datainfo[2], datainfo[3], datainfo[4], datainfo[5], datainfo[6]
        return    
    
    def HMC(self):
        print('test')

def main(nx,nobj,ncon,xl,xu,size_limit,accuracy_limit,cpath,opath, rpm4fl, ip,xname,yname,Unit, what,restart=False,ppath=None):
    global icnt
    icnt=0
    # Check PC spec. 
    print('OS                   :\t', platform.system())    
    print('OS Version           :\t', platform.version())
    print('Process information  :\t', platform.processor())    
    print('Process Architecture :\t', platform.machine())
    print('cpu count            :\t', os.cpu_count())        
    #exit()

    ## 사용자 지정 파라미터 정의 ------------------------------------------------------------------------
    ## WorkingDir. 정의
    #cpath='./output_submain'    
    if not os.path.isdir(cpath): os.mkdir(cpath)    
    if restart != False:
            try:
                temp = run_analysis.AutoCal(cpath)
                temp.clear_process(['STOP_Mechanical_1','STOP_Maxwell_2'])
            except Exception as e:
                print(f"Clear Process 실행중 에러: {e}")  
    ## 예제 정의 ===========================================#                
    # < Example Info >
    # Hock and Schittkowski 100
    # ------------------------------------------------------    
    # nx = 4
    # nobj, ncon = 1, 4
    # xl, xu = [1.0]*nx, [5.0]*nx     
    nf = nobj + ncon
    cm=communicator(nx,nf,opath=opath,rpm4fl=rpm4fl,ip=ip,DVname=xname,Yname=yname,Unit=Unit, what=what)
    ## ====================================================#

    ## AMR 입력 파라미터 선정
    # 설계변수 및 성능지수 관련 파라미터
    fl, fu           = [-10000]*nf, [10000]*nf # (Default): [-self.abnormal_num]*nf / [self.abnormal_num]*nf    
       
    # 초기 설정 관련 파라미터
    n_init           = None       # 초기 실험점 개수(Sim Default: 2*nx + 1/ Tab Default: int(3*(nx+1)*(nx+2)*0.5)) 
    batch_size       = None       # 매iter.마다 추가 실험점 개수(Default: int(min(30, 5*nx)))

    # 수렴 조건 관련 파라미터
    #accuracy_limit   = [0.05]*nf  # 목표 Nomalized test rmse 수치
    abs_avg_limit    = None       # (사용안함) 목표 average abolute error 수치(코드에 영향주지 않기 위해 음수로 설정해둠,[-1.]*nf)
    rel_avg_limit    = None       # (사용안함) 목표 average relative error 수치(코드에 영향주지 않기 위해 음수로 설정해둠,[-1.]*nf)
    #size_limit       = None       # 최대 샘플 허용수(Default: nx*500)
    no_imp_count     = None       # 연속적으로 no_imp_count 회 모델이 개선되지 않으면 강제 종료(Default: 10, 사용하지 않을 경우: -1)
    itrmop           = 2          # 연속적으로 해당횟수만큼 수렴조건 만족시 종료(Default: 1)
    
    # Outlier & Scaling Option 관련 파라미터
    process_outliers = True       # Outlier를 자동으로 제거 여부(Default: True)
    ep               = 1.e-5      # 두 점 사이의 거리가 이 값보다 같거나 작으면 같은 점(중복점)으로 간주(Default: 1.e-5)
    scaling_option   = 1
    
    # 출력 관련 파라미터
    #xname            = None       # 설계변수의 실제 이름(Default: None -> 내부에서 자동 변수명 설정)
    fname            = None       # 성능지수의 실제 이름(Default: None -> 내부에서 자동 변수명 설정)
    iprint           = True       # 결과파일 출력 여부. True/False 중 선택(Default: True)

    # AID Tab 관련 파라미터
    is_xD3           = False # Sim이면 False, Tab이면 True

    # (해당 파라미터는 고정!!)
    ntest            = -1       # Test Point 개수.
    TestFile         = None       # Test Points로 사용할 데이터가 들어있는 csv 파일.
    test2train       = False      # 최종 메타모델 생성시 test points를 train points에 포함시키려면 True, 아니면 False.

    # 기존데이터 사용 여부
    #pset = np.loadtxt(os.path.join(cpath,"pset.csv"),delimiter = ",", skiprows=1)[:,1:]    
    # Cpath에 bin 파일이 있으면 자동으로 찾아감 
    
    if restart == False: 
        pset             = None       # None이면 기존 데이터 파일 없음
    else: 
        pset = np.loadtxt(ppath,delimiter = ",")[:,:]     
        
    # 병렬 실행 여부
    is_parallel = True
    
    ## 사용자 지정 파라미터 정의 ------------------------------------------------------------------------         

    ## 변수 타입 정의 ===========================================#                  
    # Define xinfo            
    xinfo = dict()    
    for ID in range(nx): xinfo["{:d}c".format(ID+1)] = [xl[ID], xu[ID]]
    # Define "xname" & "fname" 
    #xname=[ 'TEST.CON.x{:d}'.format(i+1) for i in range(nx) ]
       
    ## 변수 타입 정의 ===========================================#              
    
    ## AMR 실행 ===========================================#              
    amr=AMRflow2(nx, nf, xinfo, 
                 fl=fl, fu=fu, pset=pset, n_init=n_init, batch_size=batch_size,                           # 초기설정 관련 파라미터      
                 accuracy_limit=accuracy_limit, abs_avg_limit=abs_avg_limit, rel_avg_limit=rel_avg_limit, # 수렴조건 관련 파라미터1 
                 size_limit=size_limit, no_imp_count=no_imp_count, itrmop=itrmop,                         # 수렴조건 관련 파라미터2
                 process_outliers=process_outliers, ep=ep,  scaling_option = scaling_option,              # Outliers, Scaling 관련 파라미터
                 xname=xname, fname=yname, is_xD3=is_xD3, is_parallel=is_parallel, cpath=cpath, iprint=iprint, # 출력     관련 파라미터
                 TestFile=TestFile, ntest=ntest, test2train=test2train                                    # (삭제예정)
                 )
    if amr.info != 0:
        raise RuntimeError(f"AMR initialization failed: {amr.info}")
    amr.run(comm=cm)

    # 최종 메타모델 생성
    fdata= cm.allrun     
    Gen_metamodel(fdata, nx, cpath, yname,bestmodel)

    if amr.info!=0:
        print(amr.info)
        return
    ## AMR 실행 ===========================================#              

    if amr.info != 0:
        raise RuntimeError(f"AMR execution failed: {amr.info}")



def AMR_setting(dir):
    if os.path.exists(dir):
        for item in os.listdir(dir):
            item_path = os.path.join(dir, item)
            # AMR_Result는 건너뛰고 나머지만 삭제
            if item != 'AMR_Result' and item != 'amrfunction.log' and item != 'base':
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
    else:
        os.makedirs(dir, exist_ok=True)
    


def Gen_metamodel(data,ndv,working_folder,oname,bestmodel):
	run_result = []
	## 문제 정의

				

	## 데이터 파일 로드1    
	data = np.array(data)
	for idx, col_idx in enumerate(range(ndv, data.shape[1])):
		data = np.loadtxt(resultpath[idx], delimiter=',')
		xset = np.array(data[:,:ndv])
		fset = np.array(data[:,ndv:])    

		## 설계 영역 정의 -> 반드시 1차원 list 형태로 입력
		xl = np.amin(xset, axis=0).tolist()
		xu = np.amax(xset, axis=0).tolist()
		if  os.path.exists(os.path.join(working_folder, "result.txt")):
			os.remove(os.path.join(working_folder, "result.txt"))

		fset_col = np.array(data[:, col_idx])
		mtype = "RBF"
		## Metamodel Option 설정
		# -------------------------------------------------------------------------------------------------
		# iprm: 정수형 파라미터
		# rprm: 실수형 파라미터
		# prgterms: Polynomial Regression 회귀항 옵션 - 'FORWARD-SW' / 'BACKWARD-SW' /  수동으로 회귀항 선택*
		#           * 수동으로 회귀항 선택 방법) 
		#            -        LR: prgterms = ([1], [1]*ndv, [0]*ndv, [0]*ndv, [0]*int(ndv*(ndv-1)/2)) 
		#            - Simple QD: prgterms = ([1], [1]*ndv, [1]*ndv, [0]*ndv, [0]*int(ndv*(ndv-1)/2)) 
		#            -   Full QD: prgterms = ([1], [1]*ndv, [1]*ndv, [0]*ndv, [1]*int(ndv*(ndv-1)/2))
		#            - Simple CB: prgterms = ([1], [1]*ndv, [1]*ndv, [1]*ndv, [1]*int(ndv*(ndv-1)/2))
		# -------------------------------------------------------------------------------------------------
		iprm, rprm, prgterms = [None]*20, [None]*20, None    
		iprm[2] = 0 # Predicted R2 계산할지 말지 여부 - 0: 계산 X / 1: 계산 O    
		iprm[3] = 1 # IMM.Log 출력 여부 - 0: 출력 X / 출력: O

		if mtype == "KRG": # Kriging
			iprm[5] = 1 # Global model type - 1: Constant / 2: Linear / 3: Simple Quadratic
			iprm[6] = 1 # Correlation Function type - 1: Exponential / 2: Gaussian / 3: General Exponential                    
		elif mtype == "RBF": # RBF
			iprm[5] = 2 # Basis function type - 1: Gaussian / 2: Multiquadric
			iprm[6] = 1 # Model type - 1: Interpolation / 2: Regression        
		elif mtype == "PR": # PR
			prgterms = 'FORWARD-SW' # 위 설명서 참고        
		elif mtype == "EDT": # EDT
			iprm[5] = 1 # Model type - 1: Hybrid / 2: Tree Bagging (TB) / 3: Random Forest (RF) / 4: Extra Trees (ET) / 5: Extreme Gradient Boosting (XGB)        
		elif mtype == "MLP": # MLP
			iprm[0] = 4 # Hyperparameter Optimizer 사용 여부 - 0: Default MLP ( [min(1.5*ndv, 200),0,...,0] ) / 4: PIAnO 탑재용 MLP 최적화 로직
			# 사용자가 직접 MLP 네트워크 아키텍처를 입력하고 싶은 경우:
			#    iprm[0] = 0으로 설정한 뒤, iprm[10] ~ iprm[19]까지 입력
		## Metamodel 생성
        # MLP 
		mmi = MMIntegrator(mtype,iprm,rprm) # 인스턴스 생성
		if mmi.info != 0: print("Initializing Failed:",mmi.info)    
		mfolder= os.path.join(working_folder, oname[idx])
		os.makedirs(mfolder, exist_ok=True)  # 폴더가 없으면 생성
		print(fset_col.min())
		print(fset_col.max())
		mmi.build(xset,fset_col,xl,xu, prgterms=prgterms, binout = True, binpath = mfolder) # 모델 생성

		if mmi.info != 0: print("Generating Metamodel Failed:",mmi.info)        
		del mmi
		mmi = MMIntegrator()
		mmi.load( binpathname = os.path.join(mfolder,"IMM.MT5") )
		

		# 결과 기록 
		print(f"결과: {oname[idx]} = {fapp[0]}")
		with open(os.path.join(working_folder, "result.txt"), "a") as f:
			f.write(f"{oname[idx]}:{fapp[0]}\n")
		del mmi 
		run_result.append(fapp[0])

	result.append(run_result)


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
    test_opath = ['D:\\work\\2025_현대multi-physics\\SW\\task']
    test_rpm4fl = 1500
    test_ip = ['10.98.40.101','10.98.40.102','10.98.40.103','10.98.40.104']
    test_dvname = ['Param1', 'Param2', 'Param3', 'Param4']
    # x: 3개 실험점, 각각 4개 설계변수 (3x4)
    test_x = np.array([
        [0.2, 0.5, 0.8, 0.3],
        [0.4, 0.6, 0.7, 0.5],
        [0.1, 0.3, 0.9, 0.2]
    ])
    # f: 3개 실험점 × 2개 목적함수 = 6개 (1D 배열)
    test_f = np.array([45.2, 32.1, 50.5, 38.9, 48.3, 35.6])
    test_unit = ['mm', 'rpm', 'N', 'C']   
    test = solving()
    cm=communicator(test_x,test_f,opath=test_opath,rpm4fl=test_rpm4fl,ip=test_ip,DVname=test_dvname,Unit=test_unit, what=what)
    cm.Analysis(test_x, test_f)
    asyncio.run(test.main(x=test_x, f=test_f, opath=test_opath, rpm4fl=test_rpm4fl, ip=test_ip, DVname=test_dvname, Unit=test_unit,what=what))