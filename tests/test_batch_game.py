"""
批量游戏测试：运行 main_zhuguosha.py 并比较输出与答案文件

使用 pytest 的参数化功能，为每个输入文件自动生成测试用例。
"""
import os
import sys
import subprocess
from pathlib import Path
from typing import Tuple, Optional, List

import pytest

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def normalize_file_content(content: str) -> List[str]:
    """标准化文件内容：去除行末空白字符和末尾空行
    
    Args:
        content: 文件内容字符串
        
    Returns:
        标准化后的行列表
    """
    lines = [line.rstrip() for line in content.splitlines()]
    # 去除文件末尾的空行
    while lines and lines[-1] == '':
        lines.pop()
    return lines


def compare_files(ans_file: Path, out_file: Path) -> Tuple[bool, Optional[str]]:
    """比较两个文件是否相同（忽略行末空白字符和末尾空行）
    
    Args:
        ans_file: 答案文件路径
        out_file: 输出文件路径
        
    Returns:
        (is_same, diff_info) - 是否相同，以及差异信息（如果有）
    """
    if not ans_file.exists():
        return False, f"答案文件不存在: {ans_file}"
    if not out_file.exists():
        return False, f"输出文件不存在: {out_file}"
    
    with open(ans_file, 'r', encoding='utf-8') as f:
        ans_content = f.read()
    
    with open(out_file, 'r', encoding='utf-8') as f:
        out_content = f.read()
    
    ans_lines = normalize_file_content(ans_content)
    out_lines = normalize_file_content(out_content)
    
    # 比较行数
    if len(ans_lines) != len(out_lines):
        return False, (
            f"行数不同: 答案文件 {len(ans_lines)} 行, "
            f"输出文件 {len(out_lines)} 行"
        )
    
    # 逐行比较
    diff_lines = []
    for i, (ans_line, out_line) in enumerate(zip(ans_lines, out_lines), start=1):
        if ans_line != out_line:
            diff_lines.append(
                f"第 {i} 行不同:\n"
                f"  答案: {repr(ans_line)}\n"
                f"  输出: {repr(out_line)}"
            )
    
    if diff_lines:
        return False, "\n".join(diff_lines)
    
    return True, None


def run_main_py(input_file: Path, timeout: int = 60) -> Tuple[int, str, str]:
    """运行 main_zhuguosha.py 处理输入文件
    
    Args:
        input_file: 输入文件路径
        timeout: 超时时间（秒）
        
    Returns:
        (returncode, stdout, stderr) - 返回码、标准输出、标准错误
    """
    main_py = PROJECT_ROOT / "main_zhuguosha.py"
    result = subprocess.run(
        [sys.executable, str(main_py), str(input_file)],
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=PROJECT_ROOT
    )
    return result.returncode, result.stdout, result.stderr


def collect_test_cases() -> List[Tuple[str, Path, Path, Path]]:
    """收集所有测试用例
    
    Returns:
        测试用例列表，每个元素为 (test_name, input_file, output_file, answer_file)
    """
    inputs_dir = PROJECT_ROOT / "HomeWork" / "inputs"
    outputs_dir = PROJECT_ROOT / "HomeWork" / "outputs"
    answers_dir = PROJECT_ROOT / "HomeWork" / "answers"
    
    if not inputs_dir.exists():
        return []
    
    test_cases = []
    for input_file in sorted(inputs_dir.glob("*.in")):
        test_name = input_file.stem
        output_file = outputs_dir / f"{test_name}.out"
        answer_file = answers_dir / f"{test_name}.ans"
        test_cases.append((test_name, input_file, output_file, answer_file))
    
    return test_cases


# 收集所有测试用例
_test_cases = collect_test_cases()


@pytest.fixture(scope="session")
def outputs_dir():
    """确保输出目录存在"""
    outputs_dir = PROJECT_ROOT / "HomeWork" / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    return outputs_dir


@pytest.mark.parametrize(
    "test_name,input_file,output_file,answer_file",
    _test_cases,
    ids=[name for name, _, _, _ in _test_cases]  # 使用测试名称作为测试ID
)
def test_game_output(
    test_name: str,
    input_file: Path,
    output_file: Path,
    answer_file: Path,
    outputs_dir: Path
):
    """测试游戏输出是否与答案文件匹配
    
    这是一个参数化测试，会为每个输入文件自动生成一个测试用例。
    
    Args:
        test_name: 测试名称（输入文件名，不含扩展名）
        input_file: 输入文件路径
        output_file: 输出文件路径
        answer_file: 答案文件路径
        outputs_dir: 输出目录（fixture）
    """
    # 运行 main_zhuguosha.py
    returncode, stdout, stderr = run_main_py(input_file)
    
    # 检查运行是否成功
    assert returncode == 0, (
        f"main_zhuguosha.py 运行失败 (返回码: {returncode})\n"
        f"标准输出:\n{stdout}\n"
        f"标准错误:\n{stderr}"
    )
    
    # 检查输出文件是否生成
    assert output_file.exists(), (
        f"输出文件未生成: {output_file}\n"
        f"标准输出:\n{stdout}\n"
        f"标准错误:\n{stderr}"
    )
    
    # 检查答案文件是否存在
    if not answer_file.exists():
        pytest.skip(f"答案文件不存在: {answer_file}")
    
    # 比较输出和答案
    is_same, diff_info = compare_files(answer_file, output_file)
    
    assert is_same, (
        f"输出与答案不匹配:\n{diff_info}\n\n"
        f"输入文件: {input_file}\n"
        f"输出文件: {output_file}\n"
        f"答案文件: {answer_file}"
    )


if __name__ == "__main__":
    # 如果直接运行此文件，执行所有测试
    pytest.main([__file__, "-v"])

