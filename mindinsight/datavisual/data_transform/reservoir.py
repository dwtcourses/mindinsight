# Copyright 2019 Huawei Technologies Co., Ltd
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
"""A reservoir sampling on the values."""

import random
import threading

from mindinsight.datavisual.common.log import logger
from mindinsight.datavisual.common.enums import PluginNameEnum
from mindinsight.utils.exceptions import ParamValueError
from mindinsight.datavisual.utils.utils import calc_histogram_bins


class Reservoir:
    """
    A container based on Reservoir Sampling algorithm.

    The newly added sample will be preserved. If the container is full, an old
    sample will be replaced randomly. The probability of each sample being
    replaced is the same.
    """

    def __init__(self, size):
        """
        A Container constructor which create a new Reservoir.

        Args:
            size (int): Container Size. If the size is 0, the container is not limited.

        Raises:
            ValueError: If size is negative integer.
        """
        if not isinstance(size, (int,)) or size < 0:
            raise ParamValueError('size must be nonnegative integer, was %s' % size)

        self._samples_max_size = size
        self._samples = []
        self._sample_counter = 0
        self._sample_selector = random.Random(0)
        self._mutex = threading.Lock()

    def samples(self):
        """Return all stored samples."""
        with self._mutex:
            return list(self._samples)

    def add_sample(self, sample):
        """
        Add a sample to Reservoir.

        Replace the old sample when the capacity is full.
        New added samples are guaranteed to be added to the reservoir.

        Args:
            sample (Any): The sample to add to the Reservoir.
        """
        with self._mutex:
            if len(self._samples) < self._samples_max_size or self._samples_max_size == 0:
                self._samples.append(sample)
            else:
                # Use the Reservoir Sampling algorithm to replace the old sample.
                rand_int = self._sample_selector.randint(
                    0, self._sample_counter)
                if rand_int < self._samples_max_size:
                    self._samples.pop(rand_int)
                    self._samples.append(sample)
                else:
                    self._samples[-1] = sample
            self._sample_counter += 1

    def remove_sample(self, filter_fun):
        """
        Remove the samples from Reservoir that do not meet the filter criteria.

        Args:
            filter_fun (Callable[..., Any]): Determines whether a sample meets
                the deletion condition.

        Returns:
            int, the number of samples removed.
        """
        remove_size = 0

        with self._mutex:
            before_remove_size = len(self._samples)
            if before_remove_size > 0:
                # remove samples that meet the filter criteria.
                self._samples = list(filter(filter_fun, self._samples))
                after_remove_size = len(self._samples)
                remove_size = before_remove_size - after_remove_size

                if remove_size > 0:
                    # update _sample_counter when samples has been removed.
                    sample_remaining_rate = float(
                        after_remove_size) / before_remove_size
                    self._sample_counter = int(
                        round(self._sample_counter * sample_remaining_rate))

        return remove_size


class _VisualRange:
    """Simple helper class to merge visual ranges."""
    def __init__(self):
        self._max = 0.0
        self._min = 0.0
        self._updated = False

    def update(self, max_val: float, min_val: float) -> None:
        """
        Merge visual range with given range.

        Args:
            max_val (float): Max value of given range.
            min_val (float): Min value of given range.

        """
        if not self._updated:
            self._max = max_val
            self._min = min_val
            self._updated = True
            return

        if max_val > self._max:
            self._max = max_val

        if min_val < self._min:
            self._min = min_val

    @property
    def max(self):
        """Gets max value of current range."""
        return self._max

    @property
    def min(self):
        """Gets min value of current range."""
        return self._min


class HistogramReservoir(Reservoir):
    """
    Reservoir for histogram, which needs updating range over all steps.

    Args:
        size (int): Container Size. If the size is 0, the container is not limited.
    """

    def samples(self):
        """Return all stored samples."""
        with self._mutex:
            # calc visual range
            visual_range = _VisualRange()
            max_count = 0
            for sample in self._samples:
                histogram = sample.value
                if histogram.count == 0:
                    # ignore empty tensor
                    continue
                max_count = max(histogram.count, max_count)
                visual_range.update(histogram.max, histogram.min)

            if visual_range.max == visual_range.min and not max_count:
                logger.warning("Max equals to min, however, count is zero. Please check mindspore "
                               "does write max and min values to histogram summary file.")

            bins = calc_histogram_bins(max_count)

            # update visual range
            logger.info("Visual histogram: min %s, max %s, bins %s, max_count %s.",
                        visual_range.min,
                        visual_range.max,
                        bins,
                        max_count)
            for sample in self._samples:
                histogram = sample.value
                histogram.set_visual_range(visual_range.max, visual_range.min, bins)

            return list(self._samples)


class ReservoirFactory:
    """Factory class to get reservoir instances."""
    def create_reservoir(self, plugin_name: str, size: int) -> Reservoir:
        """
        Creates reservoir for given plugin name.

        Args:
            plugin_name (str): Plugin name
            size (int): Container Size. If the size is 0, the container is not limited.

        Returns:
            Reservoir, reservoir instance for given plugin name.
        """
        if plugin_name == PluginNameEnum.HISTOGRAM.value:
            return HistogramReservoir(size)
        return Reservoir(size)
