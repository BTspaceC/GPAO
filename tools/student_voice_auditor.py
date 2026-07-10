#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
学生表达审核工具 (Student Voice Auditor)
----------------------------------------
【免责声明】本工具不用于AI文本鉴定，也不提供任何AI生成概率的评估。
本工具仅用于本地快速筛查文稿中存在的“空洞模板词汇”，并提供学生化的学术词汇替换建议，
帮助作业更符合真实的学术表达规范。
不需要联网，不消耗 API 额度，完全基于本地正则规则。
"""

import os
import sys
import re
import argparse

# 定义高频模板词汇及其替换建议
TEMPLATE_WORDS_DB = {
    r"诚然": {
        "suggest": "确实 / 从实际情况来看",
        "reason": "过于戏剧化的转折，极易显得行文不自然。"
    },
    r"不可否认的是": {
        "suggest": "确实 / 数据表明 / 显而易见的是",
        "reason": "无意义的口水话，学术论文应保持客观冷静。"
    },
    r"毋庸置疑": {
        "suggest": "可以确定的是 / 现有研究表明",
        "reason": "语气过于绝对，缺乏严谨学术研究所需的留余地态度。"
    },
    r"显而易见": {
        "suggest": "结果表明 / 观察发现",
        "reason": "略显主观，应让读者通过数据得出结论，而不是强加结论。"
    },
    r"值得注意的是": {
        "suggest": "进一步分析发现 / 结果显示 / 值得指出的是",
        "reason": "空洞的过渡词，容易使句式显得单调拖沓。"
    },
    r"总而言之|综上所述": {
        "suggest": "综上 / 结合上述分析 / 总体来看",
        "reason": "期末大作业中过于老套的总结词，缺乏新鲜感。"
    },
    r"扮演(?:了)?(?:核心|至关重要)的角色": {
        "suggest": "是关键影响因素 / 具有显著作用 / 对……有重要影响",
        "reason": "“扮演角色”一词被滥用，显得空洞且不专业。"
    },
    r"双刃剑": {
        "suggest": "既有积极影响也存在潜在风险 / 具有两面性",
        "reason": "讨论利弊时的万能套话，缺乏具体的机理分析。"
    },
    r"深入探讨|深刻剖析": {
        "suggest": "详细分析 / 考察 / 探讨",
        "reason": "词藻过于浮夸，大学生作业应保持谦逊，用“分析”即可。"
    },
    r"在.*的背景下": {
        "suggest": "针对……问题 / 考虑到…… / 在……中",
        "reason": "开篇万能八股句式。建议直接切入具体研究问题。"
    },
    r"正如前文所述": {
        "suggest": "如前所述 / 上述结果提示",
        "reason": "无意义的重复指示词，易被认为是拉长篇幅凑字数。"
    }
}

# 终端彩色输出辅助
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def supports_color():
    """检查当前终端是否支持彩色输出"""
    plat = sys.platform
    supported_platform = plat != 'Pocket PC' and (plat != 'win32' or 'ANSICON' in os.environ)
    is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    if plat == 'win32':
        os.system('')  # 触发 Windows 终端虚拟终端处理
    return supported_platform or is_a_tty

if not supports_color():
    class Colors:
        HEADER = BLUE = GREEN = WARNING = FAIL = ENDC = BOLD = UNDERLINE = ""

def detect_template_tone(text):
    """
    检测文本中的模板化词汇
    返回格式：[ {line_no, match_word, sentence, suggest, reason} ]
    """
    lines = text.split('\n')
    results = []
    
    for i, line in enumerate(lines):
        line_no = i + 1
        for pattern, info in TEMPLATE_WORDS_DB.items():
            matches = re.finditer(pattern, line)
            for m in matches:
                start, end = m.span()
                context_start = max(0, start - 15)
                context_end = min(len(line), end + 15)
                sentence = "..." + line[context_start:context_end].strip() + "..."
                
                matched_word = m.group(0)
                highlighted_sentence = sentence.replace(matched_word, f"{Colors.FAIL}{Colors.BOLD}{matched_word}{Colors.ENDC}")
                
                results.append({
                    "line_no": line_no,
                    "matched_word": matched_word,
                    "sentence": highlighted_sentence,
                    "suggest": info["suggest"],
                    "reason": info["reason"]
                })
    return results

def print_report(results, file_path="测试文本"):
    """打印漂亮的报告"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== 学生表达审核报告 ==={Colors.ENDC}")
    print(f"{Colors.BLUE}目标文件: {file_path}{Colors.ENDC}")
    print(f"{Colors.WARNING}【免责声明】本工具不用于AI文本鉴定，仅用于空洞模板词汇的筛查。{Colors.ENDC}")
    
    if not results:
        print(f"\n{Colors.GREEN}[OK] 未检测到明显的高频模板词汇。文字质感较为自然！{Colors.ENDC}\n")
        return True
        
    print(f"\n{Colors.WARNING}[!] 共检测到 {len(results)} 处潜在的空洞表述：{Colors.ENDC}\n")
    
    results.sort(key=lambda x: x["line_no"])
    
    for item in results:
        print(f"[-] {Colors.BOLD}第 {item['line_no']} 行{Colors.ENDC} 命中词：{Colors.FAIL}{item['matched_word']}{Colors.ENDC}")
        print(f"   上下文：{item['sentence']}")
        print(f"   >> {Colors.GREEN}修改建议：{Colors.ENDC}{item['suggest']}")
        print(f"   >> 扣分风险：{item['reason']}")
        print("-" * 50)
        
    print(f"\n{Colors.WARNING}[*] 改进建议：建议参考工作流中的辅助 Prompt 对上述段落进行具体化重写。{Colors.ENDC}\n")
    return False

def run_test():
    """运行测试模式"""
    test_text = """在数字化时代的宏大背景下，大学生耳机使用习惯扮演了至关重要的角色。
不可否认的是，长时间佩戴耳机会对听觉造成潜在损伤，这无疑是一把双刃剑。
诚然，部分同学认为戴耳机能提高专注力。值得注意的是，实验数据表明并非如此。
综上所述，我们应当深入探讨这一现象并深刻剖析其背后的机理。"""
    
    print(f"{Colors.BLUE}正在运行测试模式，待检测文本：{Colors.ENDC}")
    print("---")
    print(test_text.strip())
    print("---")
    
    results = detect_template_tone(test_text)
    print_report(results, "内置演示文本")

def main():
    parser = argparse.ArgumentParser(description="学术大作业学生表达本地审核工具")
    parser.add_argument("file", nargs="?", help="要扫描的 txt 或 md 文件路径")
    parser.add_argument("--test", action="store_true", help="运行演示测试")
    
    args = parser.parse_args()
    
    if args.test:
        run_test()
        return
        
    if not args.file:
        print(f"{Colors.BLUE}学生表达审核工具已启动。{Colors.ENDC}")
        file_path = input("请输入要检测的文稿文件绝对路径 (直接回车可运行 --test 测试模式): ").strip()
        if not file_path:
            run_test()
            return
    else:
        file_path = args.file
        
    if not os.path.exists(file_path):
        print(f"{Colors.FAIL}❌ 错误：文件 '{file_path}' 不存在。{Colors.ENDC}")
        sys.exit(1)
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, "r", encoding="gbk") as f:
                content = f.read()
        except Exception as e:
            print(f"{Colors.FAIL}❌ 错误：无法读取文件，请确保文件是 UTF-8 或 GBK 编码的文本文件。原因为: {e}{Colors.ENDC}")
            sys.exit(1)
            
    results = detect_template_tone(content)
    print_report(results, file_path)

if __name__ == "__main__":
    main()
