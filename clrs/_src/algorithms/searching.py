# Copyright 2021 DeepMind Technologies Limited. All Rights Reserved.
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

"""Searching algorithm generators.

Currently implements the following:
- Minimum
- Binary search
- Quickselect (Hoare, 1961)

See "Introduction to Algorithms" 3ed (CLRS3) for more information.

"""
# pylint: disable=invalid-name


from typing import Tuple, Union

import chex
from clrs._src import probing
from clrs._src import specs
import numpy as np


_Array = np.ndarray
_Numeric = Union[int, float]
_Out = Tuple[int, probing.ProbesDict]


def minimum(A: _Array) -> _Out:
  """Minimum."""

  chex.assert_rank(A, 1)
  probes = probing.initialize(specs.SPECS['minimum'])

  A_pos = np.arange(A.shape[0])

  probing.push(
      probes,
      specs.Stage.INPUT,
      next_probe={
          'pos': np.copy(A_pos) * 1.0 / A.shape[0],
          'key': np.copy(A)
      })

  probing.push(
      probes,
      specs.Stage.HINT,
      next_probe={
          'pred_h': probing.array(np.copy(A_pos)),
          'min_h': probing.mask_one(0, A.shape[0]),
          'i': probing.mask_one(0, A.shape[0])
      })

  min_ = 0
  for i in range(1, A.shape[0]):
    if A[min_] > A[i]:
      min_ = i

    probing.push(
        probes,
        specs.Stage.HINT,
        next_probe={
            'pred_h': probing.array(np.copy(A_pos)),
            'min_h': probing.mask_one(min_, A.shape[0]),
            'i': probing.mask_one(i, A.shape[0])
        })

  probing.push(
      probes,
      specs.Stage.OUTPUT,
      next_probe={'min': probing.mask_one(min_, A.shape[0])})

  probing.finalize(probes)

  return min_, probes

def parallel_find(x: _Numeric, A: _Array) -> _Out:
  """Parallel find."""

  chex.assert_rank(A, 1)
  probes = probing.initialize(specs.SPECS['parallel_find'])
  
  n = A.shape[0]
  T_pos = np.arange(n)
  probing.push(
      probes,
      specs.Stage.INPUT,
      next_probe={
          'pos': np.copy(T_pos),
          # 'pos': np.copy(T_pos) * 1.0 / A.shape[0],
          'key': np.copy(A),
          'target': x,
      })
  
  i = np.where(A == x)[0][0]
  
  probing.push(
      probes,
      specs.Stage.OUTPUT,
      next_probe={'return': probing.mask_one(i, n)})
    
  probing.finalize(probes)
  
  return i, probes

def parallel_search(x: _Numeric, A: _Array) -> _Out:
  """Parallel search."""

  chex.assert_rank(A, 1)
  probes = probing.initialize(specs.SPECS['parallel_search'])
  
  n = A.shape[0]
  # nodes = np.concatenate(([x], A))
  T_pos = np.arange(n) # n + 1
  
  # create sym. adj. mat with all self edges and edges between x and all others
  # adj = np.concatenate((np.transpose([np.ones(n + 1)]) , np.concatenate(([np.ones(n)], np.eye(n,n)))), 1)
# =============================================================================
#   adj_path = np.eye(n) + np.diagflat(np.ones(n - 1), 1) + np.diagflat(np.ones(n - 1), -1)
#   # path on A, connect x to each node of A
#   adj = np.concatenate((np.transpose([np.ones(n + 1)]) , np.concatenate(([np.ones(n)], adj_path))), 1)
# =============================================================================
  
  # DO I EVEN NEED ADJ OR DO I GET SAME RESULT WITH X AS GR.FT. AND ADJ_MAT INIT AS ALL ZEROS?
  # Well I need extra node anyway to reasonably encode new position of x as 1-hot
  
  #hint at x - A or sth.?!

  probing.push(
      probes,
      specs.Stage.INPUT,
      next_probe={
          'pos': np.copy(T_pos),
          # 'pos': np.copy(T_pos) * 1.0 / A.shape[0],
          'key': np.copy(A), #
          'target': x,
          # 'adj': np.copy(adj)
      })
  
  # B[i] = 1 <-> x <= A[i] 
  # by convention B[len(A)] = 1, such that lowest j at which B[j] = 1 is always desired pos. of x in A
  # this way, x has to compute min of all incoming values -> change to max (by using 1 - B and appending y at bottom)?
  # DO I GENERALLY RUN INTO TROUBLE BY HAVING X AS NODE BECAUSE OF ANTISYM. OF <?
  # B = np.ones_like(nodes)
  B = np.ones_like(A)
  i = 0
  while i < len(A) and x > A[i]:
      B[i] = 0
      i = i + 1
  
# =============================================================================
#   # B[i] = 1 <-> x >= A[i] 
#   # by convention B[len(A)] = 1, such that lowest j at which B[j] = 1 is always desired pos. of x in A
#   B = np.zeros_like(nodes)
#   i = 0
#   while i < len(A) and x >= A[i]:
#      B[i] = 1
#      i = i + 1
# =============================================================================
          
  probing.push(
      probes,
      specs.Stage.HINT,
      next_probe={
          'geq_target': np.copy(B)
          })
  
  probing.push(
      probes,
      specs.Stage.OUTPUT,
      next_probe={'return': np.array(i)}) #probing.mask_one(i, n + 1)
    
  probing.finalize(probes)
  
  return i, probes

def binary_search(x: _Numeric, A: _Array) -> _Out:
  """Binary search."""

  chex.assert_rank(A, 1)
  probes = probing.initialize(specs.SPECS['binary_search'])

  T_pos = np.arange(A.shape[0])

  probing.push(
      probes,
      specs.Stage.INPUT,
      next_probe={
          'pos': np.copy(T_pos) * 1.0 / A.shape[0],
          'key': np.copy(A),
          'target': x
      })

  probing.push(
      probes,
      specs.Stage.HINT,
      next_probe={
          'pred_h': probing.array(np.copy(T_pos)),
          'low': probing.mask_one(0, A.shape[0]),
          'high': probing.mask_one(A.shape[0] - 1, A.shape[0]),
          'mid': probing.mask_one((A.shape[0] - 1) // 2, A.shape[0]),
      })

  low = 0
  high = A.shape[0] - 1  # make sure return is always in array
  while low < high:
    mid = (low + high) // 2
    if x <= A[mid]:
      high = mid
    else:
      low = mid + 1

    probing.push(
        probes,
        specs.Stage.HINT,
        next_probe={
            'pred_h': probing.array(np.copy(T_pos)),
            'low': probing.mask_one(low, A.shape[0]),
            'high': probing.mask_one(high, A.shape[0]),
            'mid': probing.mask_one((low + high) // 2, A.shape[0]),
        })

  probing.push(
      probes,
      specs.Stage.OUTPUT,
      next_probe={'return': probing.mask_one(high, A.shape[0])})

  probing.finalize(probes)

  return high, probes


def quickselect(
    A: _Array,
    A_pos=None,
    p=None,
    r=None,
    i=None,
    probes=None,
) -> _Out:
  """Quickselect (Hoare, 1961)."""

  chex.assert_rank(A, 1)

  def partition(A, A_pos, p, r, target, probes):
    x = A[r]
    i = p - 1
    for j in range(p, r):
      if A[j] <= x:
        i += 1
        tmp = A[i]
        A[i] = A[j]
        A[j] = tmp
        tmp = A_pos[i]
        A_pos[i] = A_pos[j]
        A_pos[j] = tmp

      probing.push(
          probes,
          specs.Stage.HINT,
          next_probe={
              'pred_h': probing.array(np.copy(A_pos)),
              'p': probing.mask_one(A_pos[p], A.shape[0]),
              'r': probing.mask_one(A_pos[r], A.shape[0]),
              'i': probing.mask_one(A_pos[i + 1], A.shape[0]),
              'j': probing.mask_one(A_pos[j], A.shape[0]),
              'i_rank': (i + 1) * 1.0 / A.shape[0],
              'target': target * 1.0 / A.shape[0]
          })

    tmp = A[i + 1]
    A[i + 1] = A[r]
    A[r] = tmp
    tmp = A_pos[i + 1]
    A_pos[i + 1] = A_pos[r]
    A_pos[r] = tmp

    probing.push(
        probes,
        specs.Stage.HINT,
        next_probe={
            'pred_h': probing.array(np.copy(A_pos)),
            'p': probing.mask_one(A_pos[p], A.shape[0]),
            'r': probing.mask_one(A_pos[r], A.shape[0]),
            'i': probing.mask_one(A_pos[i + 1], A.shape[0]),
            'j': probing.mask_one(A_pos[r], A.shape[0]),
            'i_rank': (i + 1 - p) * 1.0 / A.shape[0],
            'target': target * 1.0 / A.shape[0]
        })

    return i + 1

  if A_pos is None:
    A_pos = np.arange(A.shape[0])
  if p is None:
    p = 0
  if r is None:
    r = len(A) - 1
  if i is None:
    i = len(A) // 2
  if probes is None:
    probes = probing.initialize(specs.SPECS['quickselect'])
    probing.push(
        probes,
        specs.Stage.INPUT,
        next_probe={
            'pos': np.copy(A_pos) * 1.0 / A.shape[0],
            'key': np.copy(A)
        })

  q = partition(A, A_pos, p, r, i, probes)
  k = q - p
  if i == k:
    probing.push(
        probes,
        specs.Stage.OUTPUT,
        next_probe={'median': probing.mask_one(A_pos[q], A.shape[0])})
    probing.finalize(probes)
    return A[q], probes
  elif i < k:
    return quickselect(A, A_pos, p, q - 1, i, probes)
  else:
    return quickselect(A, A_pos, q + 1, r, i - k - 1, probes)
