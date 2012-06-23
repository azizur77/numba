#! /usr/bin/env python
'''debugout.py

Example of using numba.utils.debugout() to view values in LLVM code
generated by Numba.
'''
# ______________________________________________________________________

import numpy

from numba.decorators import numba_compile
from numba.utils import debugout

# ______________________________________________________________________

def demo_function (min_x, max_x, min_y, out_arr):
    width = out_arr.shape[0]
    height = out_arr.shape[1]
    delta = (max_x - min_x) / width
    for x in range(width):
        x_val = min_x + x * delta
        for y in range(height):
            y_val = min_y + y * delta
            debugout("demo_function(): x = ", x, ", y =", y, ", x_val = ",
                     x_val, ", y_val = ", y_val)
            out_arr[x, y, 0] = x_val
            out_arr[x, y, 1] = y_val

# ______________________________________________________________________

def main (*args, **kws):
    compiled_demo_function = numba_compile(
        arg_types = ['d', 'd', 'd', [[['d']]]])(demo_function)
    control_arr = numpy.zeros((5, 5, 2))
    demo_function(-1., 1., -1., control_arr)
    test_arr = numpy.zeros_like(control_arr)
    compiled_demo_function(-1., 1., -1., test_arr)
    assert (numpy.abs(control_arr - test_arr) < 1e9).all()

# ______________________________________________________________________

if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])

# ______________________________________________________________________
# End of debugout.py
