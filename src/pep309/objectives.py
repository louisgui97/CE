from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


def rastrigin(individuals: FloatArray) -> FloatArray:
    """Evaluate Rastrigin for one vector or a matrix of individuals."""
    values = np.asarray(individuals, dtype=np.float64)
    if values.ndim not in (1, 2):
        raise ValueError("individuals deve ser um vetor ou uma matriz")
    if values.shape[-1] < 1:
        raise ValueError("cada individuo deve ter ao menos uma variavel")
    return 10.0 * values.shape[-1] + np.sum(
        values**2 - 10.0 * np.cos(2.0 * np.pi * values), axis=-1
    )
