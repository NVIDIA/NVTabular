#
# Copyright (c) 2020, NVIDIA CORPORATION.
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
#

import itertools
import json
import os
import shutil
import subprocess
import sys
from os.path import dirname, realpath

TEST_PATH = dirname(dirname(realpath(__file__)))
DATA_START = os.environ.get("DATASET_DIR", "/raid/data")


def test_criteo_basedl(tmpdir):
    input_path = os.path.join(DATA_START, "criteo/crit_int_pq")
    output_path = os.path.join(DATA_START, "criteo/crit_test")

    _run_notebook(
        tmpdir,
        os.path.join(dirname(TEST_PATH), "torch", "criteo-example-basedl.ipynb"),
        input_path,
        output_path,
        # disable rmm.reinitialize, seems to be causing issues
        batch_size=100000,
    )


def test_criteo_nvtdl(tmpdir):
    input_path = os.path.join(DATA_START, "criteo/crit_int_pq")
    output_path = os.path.join(DATA_START, "criteo/crit_test")

    _run_notebook(
        tmpdir,
        os.path.join(dirname(TEST_PATH), "torch", "criteo-example-nvtdl.ipynb"),
        input_path,
        output_path,
        # disable rmm.reinitialize, seems to be causing issues
        batch_size=100000,
    )


def test_criteo_petadl(tmpdir):
    input_path = os.path.join(DATA_START, "criteo/crit_int_pq")
    output_path = os.path.join(DATA_START, "criteo/crit_test")

    _run_notebook(
        tmpdir,
        os.path.join(dirname(TEST_PATH), "torch", "criteo-example-petastorm.ipynb"),
        input_path,
        output_path,
        # disable rmm.reinitialize, seems to be causing issues
        batch_size=100000,
    )


def test_criteo_preproc(tmpdir):
    input_path = os.path.join(DATA_START, "criteo/crit_int_pq")
    output_path = os.path.join(DATA_START, "criteo/crit_test")

    _run_notebook(
        tmpdir,
        os.path.join(dirname(TEST_PATH), "torch", "criteo-example-preproc.ipynb"),
        input_path,
        output_path,
        # disable rmm.reinitialize, seems to be causing issues
        batch_size=100000,
    )


def test_criteo_hugectr(tmpdir):
    input_path = os.path.join(DATA_START, "criteo/crit_int_pq")
    output_path = os.path.join(DATA_START, "criteo/crit_test")

    _run_notebook(
        tmpdir,
        os.path.join(dirname(TEST_PATH), "torch", "hugectr", "criteo-hugectr.ipynb"),
        input_path,
        output_path,
        # disable rmm.reinitialize, seems to be causing issues
        batch_size=100000,
    )


def _run_notebook(
    tmpdir,
    notebook_path,
    input_path,
    output_path,
    batch_size=None,
    clean_up=False,
    transform=None,
):
    #     os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)

    if batch_size and not os.environ.get("BATCH_SIZE", None):
        os.environ["BATCH_SIZE"] = str(batch_size)
    if not os.environ.get("INPUT_DATA_DIR", None):
        os.environ["INPUT_DATA_DIR"] = input_path
    if not os.environ.get("OUTPUT_DATA_DIR", None):
        os.environ["OUTPUT_DATA_DIR"] = output_path
    # make directories if not there
    if not os.path.exists(os.environ["OUTPUT_DATA_DIR"]):
        os.makedirs(os.environ["OUTPUT_DATA_DIR"])
    # read in the notebook as JSON, and extract a python script from it
    notebook = json.load(open(notebook_path))
    source_cells = [cell["source"] for cell in notebook["cells"] if cell["cell_type"] == "code"]
    lines = [
        transform(line.rstrip()) if transform else line
        for line in itertools.chain(*source_cells)
        if not (line.startswith("%") or line.startswith("!"))
    ]

    # save the script to a file, and run with the current python executable
    # we're doing this in a subprocess to avoid some issues using 'exec'
    # that were causing a segfault with globals of the exec'ed function going
    # out of scope
    script_path = os.path.join(tmpdir, "notebook.py")
    with open(script_path, "w") as script:
        script.write("\n".join(lines))
    subprocess.check_output([sys.executable, script_path])

    # clear out products
    if clean_up:
        shutil.rmtree(output_path)
