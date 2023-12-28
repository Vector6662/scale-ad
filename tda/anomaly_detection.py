from streamad.util import StreamGenerator, UnivariateDS, plot, CustomDS
from streamad.model import SpotDetector
import numpy as np
from logs import LogCluster
import pandas as pd

def detect(log_clusters: list[LogCluster]):
    data = {'values': [len(log_cluster.logMessages) for log_cluster in log_clusters],
            # 'col': [log_cluster.template for log_cluster in log_clusters],
            'label': [log_cluster.ground_truth for log_cluster in log_clusters]
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
