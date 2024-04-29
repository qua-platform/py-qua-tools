import numpy as np

dim = 3

a = np.diag(np.sqrt(np.arange(1, dim)), 1)  # excitation ladder operator
adag = np.diag(np.sqrt(np.arange(1, dim)), -1)  # relaxation ladder operator
N = np.diag(np.arange(dim))  # number operator

ident = np.eye(dim, dtype=complex)
full_ident = np.eye(dim**2, dtype=complex)

N0 = np.kron(ident, N)  # number operator, qubit 0
N1 = np.kron(N, ident)  # number operator, qubit 1

a0 = np.kron(ident, a)  # excitation ladder operator, qubit 0
a1 = np.kron(a, ident)  # excitation ladder operator, qubit 1

a0dag = np.kron(ident, adag)  # relaxation ladder operator, qubit 0
a1dag = np.kron(adag, ident)  # relaxation ladder operator, qubit 1
