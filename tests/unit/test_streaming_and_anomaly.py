"""Unit tests verifying streaming processors and anomaly estimators."""

from enterprise.anomaly.detector_part_01 import AnomalyDetectorPart01
from enterprise.streaming.processor_part_01 import StreamingProcessorPart01


def test_streaming_processor():
    res = StreamingProcessorPart01.process_event("SIG_STREAM_01_0001", count=100)
    assert "status" in res
    assert "anomaly" in res


def test_anomaly_detector():
    res = AnomalyDetectorPart01.score_anomaly("EST_TREE_01_0001", raw_score=0.999)
    assert "anomaly" in res
