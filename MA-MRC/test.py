import json, sys, os, collections, statistics, re

FN = r"c:\Users\Administrator\Desktop\MA-MRC\val.jsonl"

def normalize(s): return s.strip()

def main():
    if not os.path.exists(FN):
        print("文件不存在：", FN); return 2
    total = 0
    valid = 0
    missing = []
    json_errors = []
    answers_with_pipe = 0
    short_answers = []
    ans_counter = collections.Counter()
    q_set = set()
    dup_q = []
    answer_lens = []
    samples_bad = []

    for i, line in enumerate(open(FN, encoding='utf-8', errors='replace'), start=1):
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
        # duplicate question check
        q_norm = (q or "").strip().lower()
        if q_norm in q_set:
            dup_q.append((i, q))
        else:
            q_set.add(q_norm)
        # answer stats
        a_norm = normalize(a or "")
        ans_counter[a_norm] += 1
        answer_lens.append(len(a_norm))
        if "|" in a_norm:
            answers_with_pipe += 1
        if len(a_norm) <= 3 or a_norm.lower() in {"no","unknown","none","n/a","terminus","terminus"}:
            short_answers.append((i, a_norm))
        # heuristic: suspicious short context or weird escapes
        if len(c) < 20 or "\\n" in c or "\\\"" in c:
            samples_bad.append((i, len(c), c[:120]))
        if len(samples_bad) < 10 and (len(a_norm) <= 2 or "|" in a_norm):
            samples_bad.append(("ans_sample", i, a_norm))

    print("总行数:", total)
    print("合法 JSON 行:", valid)
    print("JSON 解析错误数:", len(json_errors))
    if json_errors:
        print("示例 JSON 错误（行, 错误）:", json_errors[:5])
    print("缺失字段行数:", len(missing))
    if missing:
        print("示例缺失字段:", missing[:5])
    print("重复问题数:", len(dup_q))
    if dup_q:
        print("示例重复问题行:", dup_q[:5])
    print("包含 '|' 的答案数量:", answers_with_pipe)
    print("不同答案总数:", len(ans_counter))
    print("最常见答案（前20）:")
    for ans, cnt in ans_counter.most_common(20):
        print(f"  {cnt:4d}  {ans!r}")
    if answer_lens:
        print("答案长度 avg/min/max:", round(statistics.mean(answer_lens),2), min(answer_lens), max(answer_lens))
    print("短答案（<=3字符 或 常见占位词）样例数:", len(short_answers))
    if short_answers:
        print("短答案示例:", short_answers[:10])
    print("其他可疑样例（上下文很短或含转义）示例（最多10）:")
    for s in samples_bad[:10]:
        print(" ", s)
    return 0

if __name__ == '__main__':
    sys.exit(main())