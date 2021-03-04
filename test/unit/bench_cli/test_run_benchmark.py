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

import unittest
import tempfile
import shutil
import os
import yaml
from .context import configuration, run_benchmark

default_cfg_fields = {
    "web": False, "tasks": [], "commit": "HEAD", "source": "testing",
    "inventory_file": "inventory_file", "mysql_host": "localhost",
    "mysql_username": "root", "mysql_password": "password",
    "mysql_database": "main", "packet_token": "AB12345",
    "packet_project_id": "AABB11", "api_key": "123-ABC-456-EFG",
    "slack_api_token": "slack-token", "slack_channel": "general",
    "config_file": "./config", "ansible_dir": "./ansible",
    "tasks_scripts_dir": "./scripts", "tasks_reports_dir": "./reports"
}

def data_to_tmp_yaml(prefix, suffix, data):
    tmpdir = tempfile.mkdtemp()
    f, tmpcfg = tempfile.mkstemp(suffix, prefix, tmpdir, text=True)
    os.write(f, yaml.dump(data).encode())
    os.close(f)
    return tmpdir, tmpcfg

class TestTaskFactoryCreateProperTaskType(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.tmpdir = tempfile.mkdtemp()
        self.task_factory = run_benchmark.TaskFactory()

    def tearDown(self) -> None:
        super().tearDown()
        shutil.rmtree(self.tmpdir)

    def test_create_tpcc(self):
        task = self.task_factory.create_task("tpcc", self.tmpdir, self.tmpdir, "inv_file", "unit_test")
        self.assertEqual("tpcc", task.name())

    def test_create_oltp(self):
        task = self.task_factory.create_task("oltp", self.tmpdir, self.tmpdir, "inv_file", "unit_test")
        self.assertEqual("oltp", task.name())

class TestCreateBenchmarkRunner(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        cfg_file_data = default_cfg_fields.copy()
        cfg_file_data.__delitem__("config_file")
        cfg_file_data.__delitem__("tasks")
        self.tmpdir, self.tmpcfg = data_to_tmp_yaml("config", ".yaml", cfg_file_data)
        cp_cfg_fields = default_cfg_fields.copy()
        cp_cfg_fields["config_file"] = self.tmpcfg
        cp_cfg_fields["tasks"] = ['oltp', 'tpcc']
        self.cfg = configuration.create_cfg(**cp_cfg_fields)
        self.config = configuration.Config(self.cfg)

    def tearDown(self) -> None:
        super().tearDown()
        shutil.rmtree(self.tmpdir)

    def test_create_benchmark_runner_all_tasks(self):
        benchmark_runner = run_benchmark.BenchmarkRunner(self.config)
        self.assertEqual(2, len(benchmark_runner.tasks))
        for i, task in enumerate(benchmark_runner.tasks):
            self.assertEqual(self.cfg["tasks"][i], task.name())

    def test_create_benchmark_runner_oltp(self):
        self.cfg["tasks"] = ['oltp']
        self.config.tasks = self.cfg["tasks"]
        benchmark_runner = run_benchmark.BenchmarkRunner(self.config)
        self.assertEqual(1, len(benchmark_runner.tasks))
        self.assertEqual(self.cfg["tasks"][0], benchmark_runner.tasks[0].name())

    def test_create_benchmark_runner_tpcc(self):
        self.cfg["tasks"] = ['tpcc']
        self.config.tasks = self.cfg["tasks"]
        benchmark_runner = run_benchmark.BenchmarkRunner(self.config)
        self.assertEqual(1, len(benchmark_runner.tasks))
        self.assertEqual(self.cfg["tasks"][0], benchmark_runner.tasks[0].name())

class TestCreationOfTaskCheckValues(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        cfg_file_data = default_cfg_fields.copy()
        cfg_file_data.__delitem__("config_file")
        cfg_file_data.__delitem__("tasks_reports_dir")
        cfg_file_data.__delitem__("ansible_dir")
        self.tmpdir, self.tmpcfg = data_to_tmp_yaml("config", ".yaml", cfg_file_data)
        cp_cfg_fields = default_cfg_fields.copy()
        cp_cfg_fields["config_file"] = self.tmpcfg
        cp_cfg_fields["tasks_reports_dir"] = self.tmpdir
        cp_cfg_fields["ansible_dir"] = self.tmpdir
        cp_cfg_fields["tasks"] = ['oltp', 'tpcc']
        self.cfg = configuration.create_cfg(**cp_cfg_fields)
        self.config = configuration.Config(self.cfg)
        self.task_factory = run_benchmark.TaskFactory()

    def tearDown(self) -> None:
        super().tearDown()
        shutil.rmtree(self.tmpdir)

    def test_create_task_check_values(self):
        tcs = [
            {"source": "unit_test","inventory_file": "inv_file","task_name": "oltp"},
            {"source": "unit_test", "inventory_file": "inv_file", "task_name": "tpcc"}
        ]
        for tc in tcs:
            task = self.task_factory.create_task(tc["task_name"], self.tmpdir, self.tmpdir, tc["inventory_file"], tc["source"])

            self.assertEqual(tc["task_name"], task.name())
            self.assertEqual(self.tmpdir, task.report_dir)
            self.assertEqual(self.tmpdir, task.ansible_dir)
            self.assertEqual(tc["inventory_file"], task.ansible_inventory_file)
            self.assertEqual(tc["source"], task.source)

            expected_ansible_build_dir = os.path.join(self.tmpdir, 'build')
            self.assertEqual(expected_ansible_build_dir, task.ansible_build_dir)

            expected_ansible_built_file = tc["inventory_file"].split('.')[0] + '-' + str(task.task_id) + '.yml'
            self.assertEqual(expected_ansible_built_file, task.ansible_built_inventory_file)
            self.assertEqual(os.path.join(expected_ansible_build_dir, expected_ansible_built_file), task.ansible_built_inventory_filepath)

            self.assertEqual(task.name().upper(), task.table_name())
            self.assertEqual(os.path.join(self.tmpdir, task.name() + "_v2.json"), task.report_path())
            self.assertEqual(os.path.join("./", task.name() + "_v2.json"), task.report_path("./"))

    def test_create_task_with_benchmark_runner_check_values(self):
        tcs = [
            {"tasks": ["oltp"]},
            {"tasks": ["tpcc"]}
        ]
        for tc in tcs:
            self.cfg["tasks"] = tc["tasks"]
            self.config.tasks = tc["tasks"]
            benchmark_runner = run_benchmark.BenchmarkRunner(self.config)

            task = benchmark_runner.tasks[0]

            self.assertEqual(self.cfg["tasks"][0], task.name())
            self.assertEqual(self.tmpdir, task.report_dir)
            self.assertEqual(self.tmpdir, task.ansible_dir)
            self.assertEqual(self.config.get_inventory_file_path(), task.ansible_inventory_file)
            self.assertEqual(self.cfg["source"], task.source)

            expected_ansible_build_dir = os.path.join(self.tmpdir, 'build')
            self.assertEqual(expected_ansible_build_dir, task.ansible_build_dir)

            expected_ansible_built_file = self.cfg["inventory_file"].split('.')[0] + '-' + str(task.task_id) + '.yml'
            self.assertEqual(expected_ansible_built_file, task.ansible_built_inventory_file)
            self.assertEqual(os.path.join(expected_ansible_build_dir, expected_ansible_built_file), task.ansible_built_inventory_filepath)

            self.assertEqual(task.name().upper(), task.table_name())
            self.assertEqual(os.path.join(self.tmpdir, task.name() + "_v2.json"), task.report_path())
            self.assertEqual(os.path.join("./", task.name() + "_v2.json"), task.report_path("./"))

if __name__ == '__main__':
    unittest.main()