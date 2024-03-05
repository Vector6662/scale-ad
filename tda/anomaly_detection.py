import numpy as np
import pandas as pd
from scipy.stats import genextreme
from streamad.model import SpotDetector
from streamad.util import CustomDS, StreamGenerator, plot

from log_structure import LogCluster, FeedBack
from rag.starter import rag_insert, rag_feedback


def detect_cdf(log_clusters: list[LogCluster]):
    data = [len(log_cluster.logMessagesCache) for log_cluster in log_clusters]
    c = -0.5
    query_threshold = 0.5
    cdfs = genextreme.cdf(data, c)
    T = 10  # range from 2 to 10
    tps = cdfs ** T / np.sum(cdfs) ** T

    # plot_cdf(data, cdfs, tps)

    for log_cluster, tp in zip(log_clusters, cdfs):
        if log_cluster.feedback.decision != 2:  # already has feedback
            continue
        if tp > query_threshold:
            # result, score, reason = openai_feedback(log_cluster)
            result, score, reason = rag_feedback(log_cluster)
            log_cluster.feedback = FeedBack(decision=1 if result == 'yes' else 0, ep=score, tp=tp, reason=reason)
            rag_insert(log_cluster)


def detect_streamad(log_clusters: list[LogCluster]):
    data = {'values': [len(log_cluster.logMessagesCache) for log_cluster in log_clusters],
            # 'col': [log_cluster.template for log_cluster in log_clusters],
            'label': [1 if log_cluster.feedback.decision == 1 else 0 for log_cluster in log_clusters]
            }
    print(data)
    ds = CustomDS(pd.DataFrame(data))
    stream = StreamGenerator(ds.data)
    model = SpotDetector()

    scores = []

    for x, log_cluster in zip(stream.iter_item(), log_clusters):
        score = model.fit_score(x)
        scores.append(score)

    data, label, date, features = ds.data, ds.label, ds.date, ds.features
    plot(data=data, scores=np.array(scores), date=date, features=features, label=label).show()
