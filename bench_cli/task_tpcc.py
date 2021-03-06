# Copyright 2021 The Vitess Authors.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#    http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import bench_cli.task as task

class TPCC(task.Task):
    def name(self) -> str:
        """
        Returns the task's name
        """
        return 'tpcc'

    def run(self, script_path: str):
        """
        Runs the task.

        @param: script_path: Path to the Ansible script's directory.

        @todo: Use the Ansible Galaxy API
        """
        os.system(os.path.join(script_path, "run-tpcc") + ' ' + self.ansible_built_inventory_filepath + ' ' + self.ansible_dir)

    def report_path(self, base: str = None) -> str:
        """
        Returns the path of the task report directory.

        @param: base: Folder to use as base for the report directory
        """
        if base is not None:
            return os.path.join(base, "tpcc_v2.json")
        return os.path.join(self.report_dir, "tpcc_v2.json")

    def table_name(self) -> str:
        """
        Returns the task's table name
        """
        return "TPCC"
