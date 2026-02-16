"""
NumPy Compatibility Layer
Ensures compatibility between NumPy 1.x and 2.x
"""
import numpy as np
from packaging import version

# Check numpy version
NUMPY_VERSION = version.parse(np.__version__)
NUMPY_2_X = NUMPY_VERSION >= version.parse("2.0.0")

# For NumPy 2.x compatibility, map deprecated types
if NUMPY_2_X:
    # NumPy 2.x removes np.int, np.float, etc.
    # Use built-in types or np.int64, np.float64
    np_int = np.int64
    np_float = np.float64
    np_bool = np.bool_
else:
    # NumPy 1.x
    np_int = np.int_
    np_float = np.float_
    np_bool = np.bool_


def ensure_numeric(arr):
    """
    Ensure array is numeric type compatible with both NumPy 1.x and 2.x
    
    Args:
        arr: Input array
        
    Returns:
        Array with compatible dtype
    """
    if isinstance(arr, np.ndarray):
        if arr.dtype == object:
            return arr.astype(np.float64)
        return arr
    return np.array(arr, dtype=np.float64)


def safe_clip(arr, min_val, max_val):
    """
    Safe clip operation that works with both NumPy versions
    
    Args:
        arr: Input array
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        Clipped array
    """
    return np.clip(arr, min_val, max_val)


print(f"NumPy Compatibility Layer loaded for NumPy {np.__version__}")
print(f"Using NumPy {'2.x' if NUMPY_2_X else '1.x'} compatibility mode")
