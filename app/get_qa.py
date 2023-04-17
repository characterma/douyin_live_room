import copy
import paddlehub as hub

QUESTION_POSTFIX = "? 下面哪些句是回复这个问题的？尽量多选几句，只输出下面选中的句子， 原样输出"
QUESTION_PROMPT = [
    {"role": "user",
     "content": f"这是一个例子，问题：十字门600升左右有没有？ {QUESTION_POSTFIX} \n这一波的话\n我们产品上面不仅做补贴\n而且活动的力度非常大\n然后十字开门600升左右没有\n直播间十字开门大的\n就是5号链有一个546升的\n这个5号链有一个546升的这一款\n然后今天我们直播间下方小时\n可以看到我们直播间的1号链接\n1号链接这一款产品是洗衣机的话\n1号链接这一款产品洗衣机的话"},
    {"role": "assistant", "content": "然后十字开门600升左右没有\n直播间十字开门大的\n就是5号链有一个546升的\n这个5号链有一个546升的这一款"},
    {"role": "user", "content": ""}
]


def get_qa(path: str) -> list:
    lac = hub.Module(name="lac")
    target_tags = set(['n', 'nv', 'PER', 'LOC', 'TIME', 'ORG', 'an', 'nw', 'm', 'v'])
    # 记录每一个qa可能的位置。 key为q的位置， a为一个list，为answer可能的开始位置。
    qa = dict()
    with open(path, encoding="utf8") as f:
        lines = f.readlines()
        begin = 0
        pos = 0
        for line in lines:
            if line.startswith("🙋:"):
                line = line.strip()
                question = line.split("]")[-1].strip()
                if len(question) == 1:
                    pos += 1
                    continue
                if line.find("小猪查理川式烤肉（河南运营中心）") >= 0:
                    pos += 1
                    continue
                begin = pos
                key_words = []

                # 对question 分词
                results = lac.lexical_analysis(texts=[question])
                # 分词后从中取出名词，动词，形容词。 其他类型的词需要干掉。
                for result in results:
                    words = result['word']
                    word_tags = result['tag']
                    i = 0
                    for word in words:
                        tag = word_tags[i]
                        if tag in target_tags:
                            key_words.append(word)
                        i += 1

                # 往后 50行找关键词。
                answer_begin = set()
                for j in range(begin + 1, begin + 100):
                    aline = lines[j]
                    for key_word in key_words:
                        if aline.find(key_word) >= 0 and not aline.startswith("🙋:"):
                            answer_begin.add(j)

                qa[begin] = answer_begin
            pos += 1



    count = 0

    qas = []

    for k, v in qa.items():
        answer = []
        values = list(v)
        values.sort()
        last_v = 0

        for answer_pos in values:
            # 连着几句话作为答案的开始，没有必要。
            if answer_pos - last_v < 10 and last_v != 0:
                continue

            for i in range(answer_pos, answer_pos + 20):
                if not lines[i].startswith("🙋:"):
                    answer.append(lines[i].strip())
            qas.append([lines[k], copy.deepcopy(answer)])
            count += 1
            answer.clear()
            last_v = answer_pos
    return qas


def get_prompts(qas: list) -> list:
    prompts = []
    for qa in qas:
        question = qa[0]
        question = question.split("]")[-1].strip()
        answers = qa[1]
        final_answer = "\n"
        for answer in answers:
            answer = answer.replace("🎙:", "") + "\n"
            final_answer += answer
        prompt = copy.deepcopy(QUESTION_PROMPT)
        prompt[-1]["content"] = f"{question}? {QUESTION_POSTFIX} {final_answer}"
        print(str(prompt))
        prompts.append(prompt)
    return prompts




if __name__ == "__main__":
    # asr_path = r"D:\pycharm\dylive\148222898325_20231319_merged.txt"
    asr_path = r"D:/data/live_data/148222898325_20231319_merged.txt"
    qas = get_qa(asr_path)
    get_prompts(qas)



