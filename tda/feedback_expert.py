import json
import os
import random
from openai import OpenAI
from config import log_metadata
import re
from log_structure import LogCluster, FeedBack

client = OpenAI()


def openai_feedback(log_cluster: LogCluster):
    samples = '\n'.join(log_cluster.get_log_messages()[0:10])
    sys_message = (
        f"Here are logs from {log_metadata}.\n"
        "Your mission is to judge whether a log message indicate system anomaly. The output must be JSON, with three fields:\n"
        "1.result, yes or no to indicate whether the log indicates a system anomaly; "
        "2.score: confidence of the result, range from 0 to 1; "
        "3.reason: explain reason of the judgement.\n"
        "example of required json output: {result:yes, score: 0.7, reason:the reason is ...}")
    user_msg = (f'Does this type of log message indicate a system anomaly?\n'
                f'log template: {log_cluster.template[0:25]}\n'
                f'examples:\n {samples}')

    response = client.chat.completions.create(
      model="gpt-3.5-turbo-1106",
      response_format={"type": "json_object"},
      messages=[
        {"role": "system", "content": sys_message},
        {"role": "user", "content": user_msg}
      ]
    )
    content = response.choices[0].message.content
    print(content)
    data = json.loads(content)
    return tuple(data.values())


def manual_feedback(log_cluster: LogCluster, tp):
    """
    ask expert for feedback, interface is console
    """
    samples = "\n".join(log_cluster.logMessagesCache[0:10])
    query_info = (f"\033[41m==================Expert Feedback==================\033[0m\n"
                  f"Does this log message indicate a system anomaly? \n"
                  f"Answer yes or no along with your confidence score ranging from 0 to 1, then explain the reasons.eg: (1,0.8)\n"
                  f"\033[32;49mTEMPLATE:\n{log_cluster.template}\n\033[0m"
                  f"samples:\n{samples}\n....\n"
                  f"\033[32;49m-->\033[0m")
    query = input(query_info)  # function to query info
    m = re.search(r'([01]?)[, ]*(0\.\d*)', query)
    # rag retrival augment generation
    assert m is not None
    g = m.groups()
    assert g[0] is not None or ''
    assert g[1] is not None or ''

    decision, ep = int(g[0]), float(g[1])
    return FeedBack(decision=decision, ep=ep, tp=tp)


def debug_feedback():
    return FeedBack(decision=random.randint(0, 1), ep=1, tp=1)