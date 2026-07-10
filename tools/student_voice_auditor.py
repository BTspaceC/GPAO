#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
学生表达审核工具 (Student Voice Auditor)
----------------------------------------
【免责声明】本工具不用于AI文本鉴定，也不提供任何AI生成概率的评估。
本工具仅用于本地快速筛查文稿中存在的“空洞模板词汇”，并提供表达提示，
帮助作业更符合真实的学术表达规范。
不需要联网，不消耗 API 额度，完全基于本地正则规则。
"""

import os
import sys
import re
import argparse

# 定义高频模板词汇及其替换提示
TEMPLATE_WORDS_DB = {
    r"诚然": {
        "suggest": "说明具体背景或实际情况，避免戏剧化转折。",
        "reason": "过于戏剧化的转折，行文不够自然。"
    },
    r"不可否认的是": {
        "suggest": "直接陈述事实，或引用数据说明。",
        "reason": "无意义的口水话，学术论文应保持客观冷静。"
    },
    r"毋庸置疑": {
        "suggest": "说明“现有研究表明”或“根据上述数据可以确定”。",
        "reason": "语气过于绝对，缺乏严谨学术研究所需的留余地态度。"
    },
    r"显而易见": {
        "suggest": "说明“观察发现”或“结果提示”。",
        "reason": "略显主观，应让读者通过数据得出结论，而不是强加结论。"
    },
    r"值得注意的是": {
        "suggest": "直接说明分析发现的结果，避免空洞的过渡句。",
        "reason": "空洞的过渡词，容易使句式显得单调拖沓。"
    },
    r"总而言之|综上所述": {
        "suggest": "结合上述分析进行具体归纳，不要只用套话。",
        "reason": "期末大作业中过于老套的总结词，缺乏新鲜感。"
    },
    r"扮演(?:了)?(?:核心|至关重要)的角色": {
        "suggest": "具体说明它与什么结果有关，以及依据来自哪里。",
        "reason": "使用了较泛化的模板表达，建议结合具体变量、过程或结果改写。"
    },
    r"双刃剑": {
        "suggest": "具体分析其积极影响与潜在风险分别是什么。",
        "reason": "讨论利弊时的万能套话，缺乏具体的机理分析。"
    },
    r"深入探讨|深刻剖析": {
        "suggest": "使用“分析”、“考察”等更中性的学术动词。",
        "reason": "词藻过于浮夸，大学生作业应保持谦逊。"
    },
    r"在.*的背景下": {
        "suggest": "直接切入具体的研究问题或具体的社会现象。",
        "reason": "开篇万能八股句式，建议直接点题。"
    },
    r"正如前文所述": {
        "suggest": "直接引用前文的具体结论，或省略该提示词。",
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
    plat = sys.platform
    supported_platform = plat != 'Pocket PC' and (plat != 'win32' or 'ANSICON' in os.environ)
    is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    if plat == 'win32':
        os.system('') 
    return supported_platform or is_a_tty

if not supports_color():
    class Colors:
        HEADER = BLUE = GREEN = WARNING = FAIL = ENDC = BOLD = UNDERLINE = ""

def detect_template_tone(text):
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
        print(f"   >> {Colors.GREEN}表达提示：{Colors.ENDC}{item['suggest']}")
        print(f"   >> 审查说明：{item['reason']}")
        print("-" * 50)
        
    print(f"\n{Colors.WARNING}[*] 改进建议：建议参考上述提示方向进行具体化重写，补充事实依据，避免机械替换同义词。{Colors.ENDC}\n")
    return False

def run_test():
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
            print(f"{Colors.FAIL}❌ 错误：无法读取文件，原因为: {e}{Colors.ENDC}")
            sys.exit(1)
            
    results = detect_template_tone(content)
    print_report(results, file_path)

if __name__ == "__main__":
    main()
