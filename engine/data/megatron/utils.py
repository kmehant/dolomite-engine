# Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.

import logging
import os
import subprocess
import sys
from enum import Enum
from typing import List

import numpy

from ...utils import log_rank_0, run_rank_n


class Split(Enum):
    train = 0
    valid = 1
    test = 2


def compile_helpers() -> None:
    """Compile C++ helper functions at runtime. Make sure this is invoked on a single process."""

    command = ["make", "-C", os.path.abspath(os.path.dirname(__file__))]
    if subprocess.run(command).returncode != 0:
        log_rank_0(logging.ERROR, "Failed to compile the C++ dataset helper functions")
        sys.exit(1)


def build_blending_indices(
    dataset_index: numpy.ndarray,
    dataset_sample_index: numpy.ndarray,
    weights: List[float],
    num_datasets: int,
    size: int,
    verbose: bool,
) -> None:
    try:
        from engine.data.megatron import helpers
    except ImportError:
        run_rank_n(compile_helpers, barrier=True)()

        from engine.data.megatron import helpers

    helpers.build_blending_indices(dataset_index, dataset_sample_index, weights, num_datasets, size, verbose)


def build_sample_idx(
    sizes: numpy.ndarray, doc_idx: numpy.ndarray, sequence_length: int, num_epochs: int, tokens_per_epoch: int
) -> numpy.ndarray:
    try:
        from engine.data.megatron import helpers
    except ImportError:
        run_rank_n(compile_helpers, barrier=True)()

        from engine.data.megatron import helpers

    return helpers.build_sample_idx(sizes, doc_idx, sequence_length, num_epochs, tokens_per_epoch)


def normalize(weights: List[float]) -> List[float]:
    """Do non-exponentiated normalization

    Args:
        weights (List[float]): The weights

    Returns:
        List[float]: The normalized weights
    """
    w = numpy.array(weights, dtype=numpy.float64)
    w_sum = numpy.sum(w)
    w = (w / w_sum).tolist()
    return w
