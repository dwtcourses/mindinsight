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

"""
Function:
    Test the various combinations based on LeNet.
"""
import os
import pytest
from mindinsight.wizard.base.utility import load_network_maker

NETWORK_NAME = 'lenet'


class TestLeNet:
    """Test LeNet Module."""

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.parametrize('params', [{
        'config': {'loss': 'SoftmaxCrossEntropyWithLogits',
                   'optimizer': 'Momentum',
                   'dataset': 'MNIST'},
        'dataset_loader_name': 'MnistDataset'
    }, {
        'config': {'loss': 'SoftmaxCrossEntropyWithLogits',
                   'optimizer': 'Adam',
                   'dataset': 'MNIST'},
        'dataset_loader_name': 'MnistDataset'
    }, {
        'config': {'loss': 'SoftmaxCrossEntropyWithLogits',
                   'optimizer': 'SGD',
                   'dataset': 'MNIST'},
        'dataset_loader_name': 'MnistDataset'
    }])
    def test_combinations(self, params):
        """Do testing."""

        network_maker_name = NETWORK_NAME
        config = params['config']
        dataset_loader_name = params['dataset_loader_name']

        network_maker = load_network_maker(network_maker_name)
        network_maker.configure(config)

        self.source_files = network_maker.generate(**config)

        self.check_scripts()
        self.check_src(dataset_loader_name, config)
        self.check_train_eval_readme(config['loss'], config['optimizer'])

    def check_src(self, dataset_name, config):
        """Check src file."""
        dataset_is_right = False
        config_optimizer_is_right = False
        network_is_right = False
        for source_file in self.source_files:
            if source_file.file_relative_path == 'src/dataset.py':
                if dataset_name in source_file.content:
                    dataset_is_right = True
            if source_file.file_relative_path == os.path.join('src', NETWORK_NAME.lower() + '.py'):
                network_is_right = True
            if source_file.file_relative_path == 'src/config.py':
                content = source_file.content

                if config['optimizer'] == 'Momentum':
                    if "'lr': 0.01" in content and \
                            "'momentum': 0.9" in content:
                        config_optimizer_is_right = True
                elif config['optimizer'] == 'SGD':
                    if "'lr': 0.01" in content:
                        config_optimizer_is_right = True
                else:
                    if "'lr': 0.001" in content:
                        config_optimizer_is_right = True
        assert dataset_is_right
        assert config_optimizer_is_right
        assert network_is_right

    def check_train_eval_readme(self, loss_name, optimizer_name):
        """Check train and eval."""

        train_is_right = False
        eval_is_right = False
        readme_is_right = False
        for source_file in self.source_files:
            if source_file.file_relative_path == 'train.py':
                content = source_file.content
                if 'LeNet5' in content and loss_name in content and optimizer_name in content:
                    train_is_right = True

            if source_file.file_relative_path == 'eval.py':
                content = source_file.content
                if 'LeNet5' in content and loss_name in content:
                    eval_is_right = True

            if source_file.file_relative_path == 'README.md':
                content = source_file.content
                if 'LeNet' in content:
                    readme_is_right = True
        assert train_is_right
        assert eval_is_right
        assert readme_is_right

    def check_scripts(self):
        """Check scripts."""

        exist_run_distribute_train = False
        exist_run_distribute_train_gpu = False
        exist_run_eval = False
        exist_run_eval_gpu = False
        exist_run_standalone_train = False
        exist_run_standalone_train_gpu = False

        for source_file in self.source_files:
            if source_file.file_relative_path == 'scripts/run_distribute_train.sh':
                exist_run_distribute_train = True
            if source_file.file_relative_path == 'scripts/run_distribute_train_gpu.sh':
                exist_run_distribute_train_gpu = True
            if source_file.file_relative_path == 'scripts/run_eval.sh':
                exist_run_eval = True
            if source_file.file_relative_path == 'scripts/run_eval_gpu.sh':
                exist_run_eval_gpu = True
            if source_file.file_relative_path == 'scripts/run_standalone_train.sh':
                exist_run_standalone_train = True
            if source_file.file_relative_path == 'scripts/run_standalone_train_gpu.sh':
                exist_run_standalone_train_gpu = True

        assert exist_run_distribute_train
        assert exist_run_distribute_train_gpu
        assert exist_run_eval
        assert exist_run_eval_gpu
        assert exist_run_standalone_train
        assert exist_run_standalone_train_gpu
