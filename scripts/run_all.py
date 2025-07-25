# scripts/run_all.py
import os, sys
import subprocess
import re
from time import sleep

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)  # 切换到项目根目录


def run_command(cmd, capture=False):
    print(f"\n🟢 执行: {cmd}")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    if capture:
        result = subprocess.run(
            cmd,
            shell=not isinstance(cmd, list),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            env=env
        )
    else:
        result = subprocess.run(
            cmd,
            shell=not isinstance(cmd, list),
            env=env
        )

    if result.returncode != 0:
        print(f"❌ 命令失败: {cmd}")
        if capture:
            print(f"命令输出：{result.stdout}")
        sys.exit(result.returncode)
    return result


if __name__ == "__main__":
    playtype = sys.argv[1] if len(sys.argv) > 1 else "gewei_sha3"
    lottery_type = sys.argv[2] if len(sys.argv) > 2 else "p5"

    while True:
        print("\n📌 === STEP 1: 生成任务 ===")
        gen_result = run_command([sys.executable, "scripts/generate_tasks.py", playtype, lottery_type], capture=True)
        gen_output = gen_result.stdout
        print(gen_output)

        no_new_task = "🟢 没有新任务插入 ➜ 外层可退出" in gen_output

        print("\n📌 === STEP 2: 回测任务 ===")

        backtest_output_lines = []
        process = subprocess.Popen(
            [sys.executable, "-u", "scripts/backtest.py", playtype, lottery_type],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8"
        )

        for line in process.stdout:
            print(line, end="")
            backtest_output_lines.append(line)

        process.wait()
        backtest_output = "".join(backtest_output_lines)

        match = re.search(r"待执行任务[:：]\s*(\d+)", backtest_output)
        pending_count = int(match.group(1)) if match else -1
        print(f"📊 当前待执行任务数量: {pending_count}")

        no_pending_task = pending_count == 0

        if no_new_task and no_pending_task:
            print("\n✅ 没有新任务且没有可执行任务 ➜ 主流程收工退出")
            run_command([sys.executable, "scripts/upload_release.py", playtype, lottery_type])
            break

        print("\n⏳ 还有任务或有新组合 ➜ 等待下一轮...")
        sleep(1)
