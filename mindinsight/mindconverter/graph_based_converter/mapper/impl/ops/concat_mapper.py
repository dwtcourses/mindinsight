# Copyright 2020 Huawei Technologies Co., Ltd.All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Mapper module."""
from mindinsight.mindconverter.graph_based_converter.constant import InputType
from ...base import ONNXToMindSporeMapper


class ConcatMapper(ONNXToMindSporeMapper):
    """Concat mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return "P.Concat"

    @staticmethod
    def _convert_params(**kwargs):
        params = kwargs['params']
        return {'axis': params['axis']}

    @staticmethod
    def _convert_trained_weights(**kwargs):
        return dict()

    @staticmethod
    def _convert_settings(**kwargs):
        input_type = InputType.LIST.value
        return {'input_type': input_type}