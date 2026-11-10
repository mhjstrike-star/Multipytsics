import csv
import os
import platform
import asyncio
import logging
import numpy as np

from shutil                         import copytree
from pathlib                        import Path
from tempfile                       import NamedTemporaryFile, TemporaryDirectory
from AIDPreprocessing               import AIDPrep

def generate_screening_design(design_variables, sample_count):
    if len(design_variables) < 2:
        raise ValueError("Near OA Screening에는 설계변수를 두 개 이상 선택해 주세요.")
    if type(sample_count) is not int or sample_count < 3:
        raise ValueError("실험점 수는 3 이상의 정수여야 합니다.")
    
    names = [variable['NAME'].strip() for variable in design_variables]
    if any(not name for name in names) or len(set(names)) != len(names):
        raise ValueError("설계변수 이름은 비어 있거나 중복될 수 없습니다.")

    bounds = np.array([[variable['LV'], variable['UV']] for variable in design_variables], dtype=float)
    lower, upper = bounds.T
    middle = lower / 2 + upper / 2
    if not np.isfinite(bounds).all() or not ((lower < middle) & (middle < upper)).all():
        raise ValueError("각 설계변수에 서로 다른 하한·중간값·상한을 지정해 주세요.")
    levels = np.column_stack((lower, middle, upper))

    import OAG
    database = Path(OAG.__file__).parent / 'externals' / 'OADB'
    with TemporaryDirectory(prefix='screening-oag-') as scratch:
        work_dir = Path(scratch)
        # OAG opens its database for write access even when querying OA sizes.
        writable_database = work_dir / 'OADB'
        copytree(database, writable_database)
        generator = OAG.OAgenerator(nLv=[3] * len(names), cpath=work_dir.as_posix() + '/', dpath=writable_database.as_posix() + '/',)
        status, available_counts, _, _ = generator.generator(0)
        if status not in (0, 1, 2, 3):
            raise RuntimeError(f"가능한 OA 실험점 수를 조회하지 못했습니다 (OAG 상태 코드 {status}).")
        status, _, level_codes, orthogonality = generator.generator(sample_count)
        if status in (1, 2, 3):
            raise ValueError(f"ToolBox가 {sample_count}점에 사용할 실험표를 결정하지 못했습니다. 다른 실험점 수를 입력해 주세요 (OAG 상태 코드 {status}).")
        if status != 0:
            raise ValueError(f"실험점 {sample_count}개를 생성할 수 없습니다 (OAG 상태 코드 {status}).")

    level_codes = np.asarray(level_codes)
    actual_count, remaining = divmod(level_codes.size, len(names))
    if remaining or not 0 < actual_count <= sample_count:
        raise RuntimeError("ToolBox가 유효하지 않은 크기의 실험표를 반환했습니다.")
    if not np.issubdtype(level_codes.dtype, np.integer) or ((level_codes < 1) | (level_codes > 3)).any():
        raise RuntimeError("ToolBox가 1~3 범위를 벗어난 수준 번호를 반환했습니다.")

    # The Windows OAG wrapper can pack two 32-bit row counts into one integer.
    oa_counts = sorted({count for value in available_counts for count in (int(value) & 0xffffffff, int(value) >> 32) if count > 0})
    points = levels[np.arange(len(names)), level_codes.reshape(actual_count, len(names)) - 1]
    return {
        'names': names,
        'points': points,
        'orthogonality': float(orthogonality),
        'oa_counts': oa_counts,
    }


def save_screening_run_table(result_dir, headers, rows):
    path = result_dir / 'Runcount_Total.csv'
    # Keep an existing result intact if writing fails or Excel has it open.
    temporary_path = None
    try:
        with NamedTemporaryFile(
            mode='w', encoding='utf-8-sig', newline='', dir=result_dir, delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
            writer = csv.writer(temporary)
            writer.writerow(headers)
            writer.writerows(rows)
        temporary_path.replace(path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return path


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