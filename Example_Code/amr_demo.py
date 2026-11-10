import csv
import multiprocessing
import os
import re
import sys
import tempfile
import types
from pathlib import Path

DEMO_DIR = Path(__file__).resolve().parent
PROJECT_DIR = DEMO_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

from functions.main_functions import load_OV_list


class DemoAutoCal:
    def __init__(self, work_dir):
        self.work_dir = work_dir

    def get_X(self):
        pass

    def clear_process(self, names):
        pass

    def cal_response(self, input_file, *, rpm4FL, what, ip):
        # The normal solver passes one tab-separated row with values and units.
        input_path = Path(input_file)
        lines = input_path.read_text(encoding="utf-8").splitlines()
        values = [
            float(re.match(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?", value).group())
            for value in lines[1].split("\t")
        ]
        response = sum((index + 1) * value for index, value in enumerate(values))
        outputs = [row["NAME"] for row in load_OV_list()]

        result_dir = input_path.parent / "geom1"
        result_dir.mkdir()
        with (result_dir / "result.csv").open("w", encoding="utf-8", newline="") as result:
            writer = csv.writer(result)
            writer.writerow([*outputs, "OKNG"])
            writer.writerow([
                *(f"{100 + index + response * 0.01:.10f}" for index, _ in enumerate(outputs)),
                "OK",
            ])

        markers = {
            "Maxwell": "step3 is finished\n",
            "Mechanical": "step4 is finished\n",
            "All": "step3 is finished\nstep4 is finished\n",
        }
        (result_dir / "progress.txt").write_text(markers[what], encoding="utf-8")


# Both the window and the spawned AMR process load this launcher.
# Replace the customer module only in these Python processes.
from functions import amr_functions, solve

customer = types.ModuleType("functions.run_analysis")
customer.AutoCal = DemoAutoCal
amr_functions.run_analysis = customer
solve.run_analysis = customer


def main():
    smoke = "--smoke" in sys.argv
    if smoke:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"

    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QTableWidgetItem
    from Main import MainWindow, apply_modern_stylesheet

    runs_dir = DEMO_DIR / "runs"
    runs_dir.mkdir(exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix="run-", dir=runs_dir))
    source_dir = run_dir / "input"
    source_dir.mkdir()
    (source_dir / "demo.txt").write_text("Synthetic inputs for the AMR demo.\n", encoding="utf-8")
    os.chdir(run_dir)
    print(f"Demo run folder: {run_dir}", flush=True)

    app = QApplication([sys.argv[0]])
    apply_modern_stylesheet(app)
    window = MainWindow()
    window.setWindowTitle("AMR 테스트 - 모의 해석")
    main_page = window.pages["Main"]
    amr_page = window.pages["AMR"]

    # Prepare one variable and one output using the normal Main confirmation flow.
    main_page.result_folder_input.setText(str(source_dir))
    main_page.uiwang_ip_input.setText("127.0.0.1")
    main_page.uiwang_node_input.setValue(1)
    main_page.gwangju_ip_input.setText("127.0.0.1")
    main_page.gwangju_node_input.setValue(0)
    main_page.table.setItem(0, 1, QTableWidgetItem("90"))
    main_page.table.setItem(0, 2, QTableWidgetItem("110"))
    main_page.table.cellWidget(0, 4).setCurrentText("선택")
    main_page.output_table.cellWidget(0, 2).setCurrentText("선택")
    main_page.on_confirm_design_variables()
    if not window.DV or not window.OV:
        raise RuntimeError("Could not prepare the demo variables from ANALYSIS_DATA.")

    main_page.setEnabled(False)  # Keep the demo in its own working directory.
    amr_page.max_exp_spinbox.setValue(20)
    window.switch_page("AMR")
    banner = QLabel("모의 해석 전용  |  고객사 AutoCal 없이 실행")
    banner.setStyleSheet("background: #f2c14e; color: #171717; padding: 8px; font-weight: bold;")
    amr_page.layout().insertWidget(0, banner)
    amr_page.log_display.appendPlainText(f"모의 해석 준비 완료. 실행을 눌러 주세요.\n작업 폴더 {run_dir / 'task'}")

    def stop_worker():
        worker = amr_page.amr_worker
        if worker is not None and worker.is_alive():
            worker.terminate()
            worker.join(timeout=5)

    app.aboutToQuit.connect(stop_worker)
    if smoke:
        def verify_result():
            if amr_page.amr_worker is not None:
                return
            result = run_dir / "task" / "AMR_Result" / "Restart.csv"
            log = amr_page.log_display.toPlainText()
            if result.is_file() and "실행 완료" in log:
                rows = len(result.read_text(encoding="utf-8").splitlines())
                print(f"Native AMR completed with synthetic data ({rows} samples).", flush=True)
                app.exit(0)
            else:
                print(log, flush=True)
                app.exit(1)

        poll = QTimer()
        poll.timeout.connect(verify_result)
        execute_button = next(button for button in amr_page.findChildren(QPushButton) if button.text() == "실행")
        QTimer.singleShot(0, execute_button.click)
        poll.start(250)
        QTimer.singleShot(90000, lambda: app.exit(1))
    window.show()
    if not smoke:
        window.raise_()
        window.activateWindow()
    return app.exec()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    sys.exit(main())
