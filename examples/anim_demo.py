# -----------------------------------------------------------------------------
# Python & OpenGL for Scientific Visualization
# www.labri.fr/perso/nrougier/python+opengl
# Copyright (c) 2018, Nicolas P. Rougier
# Distributed under the 2-Clause BSD License.
# -----------------------------------------------------------------------------
import sys
import ctypes
import numpy as np
import moderngl





n = 2048
T = np.linspace(0, 20 * 2 * np.pi, n, dtype=np.float32)
R = np.linspace(.1, np.pi - .1, n, dtype=np.float32)
X = np.cos(T) * np.sin(R)
Y = np.sin(T) * np.sin(R)
Z = np.cos(R)
P = np.dstack((X, Y, Z)).squeeze()

print(P)