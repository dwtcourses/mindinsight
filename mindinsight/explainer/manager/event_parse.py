# Copyright 2020 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""EventParser for summary event."""
from collections import namedtuple
from typing import Dict, Iterable, List, Optional, Tuple

from mindinsight.explainer.common.enums import PluginNameEnum
from mindinsight.explainer.common.log import logger
from mindinsight.utils.exceptions import UnknownError

_IMAGE_DATA_TAGS = {
    'image_data': PluginNameEnum.IMAGE_DATA.value,
    'ground_truth_label': PluginNameEnum.GROUND_TRUTH_LABEL.value,
    'inference': PluginNameEnum.INFERENCE.value,
    'explanation': PluginNameEnum.EXPLANATION.value
}


class EventParser:
    """Parser for event data."""

    def __init__(self, job):
        self._job = job
        self._sample_pool = {}

    def clear(self):
        """Clear the loaded data."""
        self._sample_pool.clear()

    def parse_metadata(self, metadata) -> Tuple[List, List, List]:
        """Parse the metadata event."""
        explainers = list(metadata.explain_method)
        metrics = list(metadata.benchmark_method)
        labels = list(metadata.label)
        return explainers, metrics, labels

    def parse_benchmark(self, benchmark) -> Dict:
        """Parse the benchmark event."""
        imported_benchmark = {}
        for explainer_result in benchmark:
            explainer = explainer_result.explain_method
            total_score = explainer_result.total_score
            label_score = explainer_result.label_score

            explainer_benchmark = {
                'explainer': explainer,
                'evaluations': EventParser._total_score_to_dict(total_score),
                'class_scores': EventParser._label_score_to_dict(label_score, self._job.labels)
            }
            imported_benchmark[explainer] = explainer_benchmark
        return imported_benchmark

    def parse_sample(self, sample: namedtuple) -> Optional[namedtuple]:
        """Parse the sample event."""
        sample_id = sample.image_id

        if sample_id not in self._sample_pool:
            self._sample_pool[sample_id] = sample
            return None

        for tag in _IMAGE_DATA_TAGS:
            try:
                if tag == PluginNameEnum.INFERENCE.value:
                    self._parse_inference(sample, sample_id)
                elif tag == PluginNameEnum.EXPLANATION.value:
                    self._parse_explanation(sample, sample_id)
                else:
                    self._parse_sample_info(sample, sample_id, tag)
            except UnknownError as ex:
                logger.warning("Parse %s data failed within image related data,"
                               " detail: %r", tag, str(ex))
                continue

        if EventParser._is_sample_data_complete(self._sample_pool[sample_id]):
            return self._sample_pool.pop(sample_id)
        if EventParser._is_ready_for_display(self._sample_pool[sample_id]):
            return self._sample_pool[sample_id]
        return None

    def _parse_inference(self, event, sample_id):
        """Parse the inference event."""
        self._sample_pool[sample_id].inference.ground_truth_prob.extend(
            event.inference.ground_truth_prob)
        self._sample_pool[sample_id].inference.predicted_label.extend(
            event.inference.predicted_label)
        self._sample_pool[sample_id].inference.predicted_prob.extend(
            event.inference.predicted_prob)

    def _parse_explanation(self, event, sample_id):
        """Parse the explanation event."""
        if event.explanation:
            for explanation_item in event.explanation:
                new_explanation = self._sample_pool[sample_id].explanation.add()
                new_explanation.explain_method = explanation_item.explain_method
                new_explanation.label = explanation_item.label
                new_explanation.heatmap = explanation_item.heatmap

    def _parse_sample_info(self, event, sample_id, tag):
        """Parse the event containing image info."""
        if not getattr(self._sample_pool[sample_id], tag):
            setattr(self._sample_pool[sample_id], tag, getattr(event, tag))

    @staticmethod
    def _total_score_to_dict(total_scores: Iterable):
        """Transfer a list of benchmark score to a list of dict."""
        evaluation_info = []
        for total_score in total_scores:
            metric_result = {
                'metric': total_score.benchmark_method,
                'score': total_score.score}
            evaluation_info.append(metric_result)
        return evaluation_info

    @staticmethod
    def _label_score_to_dict(label_scores: Iterable, labels: List[str]):
        """Transfer a list of benchmark score."""
        evaluation_info = [{'label': label, 'evaluations': []}
                           for label in labels]
        for label_score in label_scores:
            metric = label_score.benchmark_method
            for i, score in enumerate(label_score.score):
                label_metric_score = {
                    'metric': metric,
                    'score': score}
                evaluation_info[i]['evaluations'].append(label_metric_score)
        return evaluation_info

    @staticmethod
    def _is_sample_data_complete(image_container: namedtuple) -> bool:
        """Check whether sample data completely loaded."""
        required_attrs = ['image_id', 'image_data', 'ground_truth_label', 'inference', 'explanation']
        for attr in required_attrs:
            if not EventParser.is_attr_ready(image_container, attr):
                return False
        return True

    @staticmethod
    def _is_ready_for_display(image_container: namedtuple) -> bool:
        """
        Check whether the image_container is ready for frontend display.

        Args:
            image_container (nametuple): container consists of sample data

        Return:
            bool: whether the image_container if ready for display
        """
        required_attrs = ['image_id', 'image_data', 'ground_truth_label', 'inference']
        for attr in required_attrs:
            if not EventParser.is_attr_ready(image_container, attr):
                return False
        return True

    @staticmethod
    def is_attr_ready(image_container: namedtuple, attr: str) -> bool:
        """
        Check whether the given attribute is ready in image_container.

        Args:
            image_container (nametuple): container consist of sample data
            attr (str): attribute to check

        Returns:
            bool, whether the attr is ready
        """
        if getattr(image_container, attr, False):
            return True
        return False
