from streamad.util import StreamGenerator, UnivariateDS, plot, CustomDS
from streamad.model import SpotDetector
import numpy as np


def detect(data: list):
    ds = CustomDS(np.array(data))
    stream = StreamGenerator(ds.data)
    model = SpotDetector()

    scores = []

    for x in stream.iter_item():
        score = model.fit_score(x)
        scores.append(score)

    data, label, date, features = ds.data, ds.label, ds.date, ds.features
    plot(data=data, scores=scores, date=date, features=features, label=label).show()
