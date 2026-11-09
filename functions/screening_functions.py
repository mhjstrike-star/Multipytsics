import numpy as np
import os
from os import sys
import platform
import asyncio
import logging
from AIDPreprocessing import AIDPrep

def main():
        
    # 입력파라미터 설정 ----------------------------        
    iprint = True    
    # --------------------------------------------        
    if not os.path.exists(cpath):
        os.makedirs(cpath)
    
    nexp, nx, nf = 60, 3, 3   
    datafile_name = 'Threebar_ex.csv'
    
    pset = [ line.replace("\n","").split(",") for line in open(os.path.join(cpath, datafile_name), "r").readlines() ] # 2D        
    pset_1d = list()
    for line in pset:
        pset_1d += line
    pset = pset_1d
    indices = list(range(1,nexp+1))
            
    xname = ["A1","A2","Length"]
    fname = ["Volume","Sigma1","Sigma2"]    
    xinfo = {"1d":[1,2,3,4],"2c":[1.0,20.0],"3c":[80.0,100.0]}    
    fl, fu = None, None

    aidprep = AIDPrep(nx=nx, nf=nf, xinfo=xinfo, fl=fl, fu=fu, xname=xname, fname=fname, cpath=cpath, iprint=iprint)
    
    # (0) 데이터를 객체변수로 저장(무조건 실행)
    aidprep.store_data_to_object(pset, indices)        
    
    # (1) 1D 이상점 탐지
    outlier1D_idx = aidprep.find_1D_outlier(alpha = None)
        
    # (2) 중복점 체크
    duplct_idx = aidprep.find_duplct(ep = None)
    
    # (3) 2D 이상점 탐지    
    outlier2D_idx = aidprep.find_2D_outlier(residual_threshold=None, random_state=None)
    
    # (4) 데이터 부족체크 - Screening에서만(추가 데이터 가이드 필요)
    del_idx = list()
    for fid in range(nf):
        if aidprep.fname[fid] in outlier1D_idx.keys(): del_idx += outlier1D_idx[aidprep.fname[fid]]
        if aidprep.fname[fid] in outlier2D_idx.keys(): del_idx += outlier2D_idx[aidprep.fname[fid]]
    for idx_ in duplct_idx:
        del_idx += idx_
    del_idx = np.unique(del_idx).tolist()
    lackdata_info, recommended_xset = aidprep.check_lack_of_data(del_idx)    

    # 리포트 생성을 위한 파일 쓰기
    del_idx = np.where(np.isin(aidprep.indices, del_idx))[0]
    refined_pset = np.delete( aidprep.pset, del_idx, axis = 0)
    refined_indices = np.delete( aidprep.indices, del_idx, axis = 0)    
    aidprep.write_resultfile_for_report(add_data_by_logic = False, refined_pset = refined_pset, refined_indices = refined_indices)
    
    exit()


if __name__ == '__main__':
    main()
    