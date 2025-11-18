import json, sys, os, collections, statistics, re

FN = r"c:\Users\Administrator\Desktop\MA-MRC\val.jsonl"

def normalize(s): return (s or "").strip()

def analyze():
    if not os.path.exists(FN):
        print("文件不存在：", FN); return None
    total = valid = 0
    missing = []
    json_errors = []
    answers_with_pipe = 0
    short_answers = []
    ans_counter = collections.Counter()
    q_set = set()
    dup_q = []
    answer_lens = []
    samples_bad = []
    answer_details = []   # (line, question, context, a_norm, parts)

    with open(FN, encoding='utf-8', errors='replace') as fh:
        for i, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                obj = json.loads(line)
            except Exception as e:
                json_errors.append((i, str(e), line[:200]))
                continue
            valid += 1
            q = obj.get("question")
            c = obj.get("context")
            a = obj.get("answer")
            if q is None or c is None or a is None:
                missing.append((i, {"question": q is None, "context": c is None, "answer": a is None}))
            q_norm = (q or "").strip().lower()
            if q_norm in q_set:
                dup_q.append((i, q))
            else:
                q_set.add(q_norm)
            a_norm = normalize(a)
            parts = [p.strip() for p in a_norm.split('|') if p.strip()]
            answer_details.append((i, q, c, a_norm, parts))

            ans_counter[a_norm] += 1
            answer_lens.append(len(a_norm))
            if "|" in a_norm:
                answers_with_pipe += 1
            if len(a_norm) <= 3 or a_norm.lower() in {"no", "unknown", "none", "n/a", "terminus"}:
                short_answers.append((i, a_norm))
            if (c or "") and (len(c) < 20 or "\\n" in c or '\\"' in c):
                samples_bad.append((i, len(c), (c or "")[:120]))
            if len(samples_bad) < 10 and (len(a_norm) <= 2 or "|" in a_norm):
                samples_bad.append(("ans_sample", i, a_norm))

    stats = {
        "total": total,
        "valid": valid,
        "json_errors": json_errors,
        "missing": missing,
        "dup_q": dup_q,
        "answers_with_pipe": answers_with_pipe,
        "ans_counter": ans_counter,
        "answer_lens": answer_lens,
        "short_answers": short_answers,
        "samples_bad": samples_bad,
        "answer_details": answer_details
    }
    return stats

def print_stats(stats):
    if stats is None:
        return 2
    print("总行数:", stats["total"])
    print("合法 JSON 行:", stats["valid"])
    print("JSON 解析错误数:", len(stats["json_errors"]))
    if stats["json_errors"]:
        print("示例 JSON 错误（行, 错误）:", stats["json_errors"][:5])
    print("缺失字段行数:", len(stats["missing"]))
    if stats["missing"]:
        print("示例缺失字段:", stats["missing"][:5])
    print("重复问题数:", len(stats["dup_q"]))
    if stats["dup_q"]:
        print("示例重复问题行:", stats["dup_q"][:5])
    print("包含 '|' 的答案数量:", stats["answers_with_pipe"])
    print("不同答案总数:", len(stats["ans_counter"]))
    print("最常见答案（前20）:")
    for ans, cnt in stats["ans_counter"].most_common(20):
        print(f"  {cnt:4d}  {ans!r}")
    if stats["answer_lens"]:
        print("答案长度 avg/min/max:", round(statistics.mean(stats["answer_lens"]),2), min(stats["answer_lens"]), max(stats["answer_lens"]))
    print("短答案（<=3字符 或 常见占位词）样例数:", len(stats["short_answers"]))
    if stats["short_answers"]:
        print("短答案示例:", stats["short_answers"][:10])
    print("其他可疑样例（上下文很短或含转义）示例（最多10）:")
    for s in stats["samples_bad"][:10]:
        print(" ", s)

    # 统计每行答案数量
    answer_counts = [len(parts) for (_, _, _, _, parts) in stats["answer_details"]]
    if answer_counts:
        print("每行答案数量 — 平均值: {:.2f}, 最大值: {}, 最小值: {}".format(
            statistics.mean(answer_counts), max(answer_counts), min(answer_counts)
        ))
    else:
        print("未统计到答案数量。")
    return 0

def show_max_answer_samples(stats, limit=20):
    if stats is None:
        print("未能读取数据文件。"); return 2
    details = stats["answer_details"]
    if not details:
        print("没有样例可显示。"); return 0
    max_cnt = max(len(parts) for (_, _, _, _, parts) in details)
    print(f"\n答案个数最多的样例（个数 = {max_cnt}），最多显示 {limit} 条：")
    printed = 0
    for ln, q, c, a_norm, parts in details:
        if len(parts) == max_cnt:
            print("=" * 80)
            print(f"行 {ln}  个数 {len(parts)}")
            print("问题:", (q or "")[:200])
            print("答案列表:", parts)
            print("原始答案字段:", a_norm)
            print("上下文（前400字符）:", (c or "")[:400])
            printed += 1
            if printed >= limit:
                break
    if printed == 0:
        print("未找到符合条件的样例。")
    return 0

def show_examples(stats, limit=10):
    if stats is None:
        print("未能读取数据文件。"); return 2
    printed = 0
    for ln, q, c, a_norm, parts in stats["answer_details"]:
        print("=" * 80)
        print(f"行 {ln}:")
        print("问题:", (q or "")[:200])
        print("答案:", a_norm)
        print("答案列表:", parts)
        print("上下文（前400字符）:", (c or "")[:400])
        printed += 1
        if printed >= limit:
            break
    if printed == 0:
        print("未找到有效样例。")
    else:
        print("=" * 80)
        print(f"已打印 {printed} 条样例。")
    return 0

def usage():
    print("用法:")
    print("  python test1.py                   # 打印统计摘要")
    print("  python test1.py --show-max-answers [limit]")
    print("  python test1.py --show-examples [limit]")
    return 0

if __name__ == '__main__':
    stats = analyze()
    if len(sys.argv) == 1:
        sys.exit(print_stats(stats))
    if sys.argv[1] == '--show-max-answers':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 20
        sys.exit(show_max_answer_samples(stats, limit=limit))
    if sys.argv[1] == '--show-examples':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 10
        sys.exit(show_examples(stats, limit=limit))
    # unknown option
    usage()
    sys.exit(1)