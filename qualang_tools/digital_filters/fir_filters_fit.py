import matplotlib.pylab as plt
import numpy as np
from scipy import linalg
from scipy.interpolate import interp1d
from scipy.signal import lfilter
from typing import List, Tuple, Literal
from typing import Optional
from numpy.typing import ArrayLike
import netCDF4 as nc

#%%
def conv_causal(v: ArrayLike, h: ArrayLike, N: Optional[int] = None) -> np.ndarray:
    """
    Perform a causal (one-sided) convolution of input signal v with filter h.

    Parameters
    ----------
    v : array-like
        Input sequence (e.g., signal to be filtered)
    h : array-like
        Impulse response (filter coefficients)
    N : int or None, optional
        Number of output points to return. If None, returns the convolution up to the length of v.

    Returns
    -------
    y : ndarray
        The result of the causal convolution of v with h, truncated to N or len(v) samples.
    """
    v = np.asarray(v, dtype=float)
    h = np.asarray(h, dtype=float)
    y = np.convolve(v, h, mode='full')
    
    return y[: (len(v) if N is None else N)]


def build_toeplitz_matrix(v, L):
    """
    Construct a Toeplitz matrix from input sequence v for FIR system identification.

    Parameters
    ----------
    v : array-like
        Input sequence (stimulus to system).
    L : int
        Number of filter coefficients (FIR length).

    Returns
    -------
    V : ndarray, shape (N, L)
        Toeplitz matrix such that each row forms a lagged vector of v,
        suitable for linear convolution: phi ≈ V @ h.
    """
    v = np.asarray(v, float)
    N = len(v)
    
    return linalg.toeplitz(c=v, r=np.concatenate([[v[0]], np.zeros(L - 1)]))


def resample_to_target_rate(
    data: ArrayLike, 
    original_Ts: float, 
    target_Ts: float, 
    kind: str = 'cubic'
    ) -> np.ndarray:
    """
    Resample time-domain data to a specified target sampling rate.
    
    Parameters
    ----------
    data : array-like
        The original time-domain data
    original_Ts : float
        The original sampling time, in nanoseconds
    target_Ts : float
        The target sampling time, in nanoseconds
    kind : str
        Interpolation kind ('linear', 'cubic', etc.)
    
    Returns
    -------
    resampled : numpy.ndarray
        The data interpolated onto the target sampling rate grid
    """
    
    data = np.asarray(data)
    N = len(data)
    t_original = np.arange(N) * original_Ts
    max_time = t_original[-1]
    
    num_samples = int(np.floor(max_time / target_Ts)) + 1
    t_target = np.arange(num_samples) * target_Ts
    t_target = t_target[t_target <= max_time]
    
    interp_fun = interp1d(t_original, data, kind=kind, fill_value="extrapolate", bounds_error=False)
    return interp_fun(t_target)

FIR_filter_coefficient =[]

def fit_fir(
    phi: ArrayLike, 
    v: ArrayLike, 
    L: int = 0.5, 
    Ts: float = 0.5, 
    lam1: float = 1e-2,
    lam2: float = 1e-2, 
    tail_ns: Optional[float] = None
    ) -> np.ndarray:
    """
    Fit a finite impulse response (FIR) filter to data. Solves for FIR filter coefficients `h` 
    with length `L` such that `phi ≈ V @ h`, where `V` is the Toeplitz matrix constructed from 
    input `v`.

    Parameters
    ----------
    phi : array_like
        response signal (1D array).
    v : array_like
        Input signal to be filtered (1D array).
    L : int
        Number of FIR filter taps (length of FIR filter).
    Ts : float, optional
        Sampling time (in nanoseconds). Default is 0.5.
    lam1 : float, optional
        Regularization parameter for the identity matrix. Default is 1e-2.
    lam2 : float, optional
        Regularization parameter for exponential tail. Default is 1e-2.
    tail_ns : float, optional
        Time constant (in nanoseconds) for tail regularization. If None, computed as (L*Ts)/3.0.

    Returns
    -------
    h : ndarray
        Fitted FIR filter coefficients (1D array of length L).
    """
    phi = np.asarray(phi, float)
    v = np.asarray(v, float)
    V = build_toeplitz_matrix(v, L)

    if tail_ns is None:
        tail_ns = (L*Ts)/3.0
    idx = np.arange(L)
    x = np.exp(idx * Ts / tail_ns)

    A = V.T @ V + lam1*np.eye(L) + lam2*np.diag(x)
    b = V.T @ phi
    h = linalg.solve(A, b, assume_a='pos')
    
    return h


def optimize_fir_parameters(
    response: ArrayLike, 
    Ts: float = 0.5,
    L_values: List[int] = [16, 20, 24, 28, 32, 40, 48],
    lam1_values: List[float] = [1e-5, 1e-4, 1e-3, 1e-2, 1e-1],
    lam2_values: List[float] = [1e-5, 1e-4, 1e-3, 1e-2, 1e-1]
    ) -> Tuple[List[dict], float, dict, np.ndarray, np.ndarray]:
    """
    Optimize FIR extraction parameters (L, lam1, lam2) to minimize the reconstruction error
    between the measured response and the reconstructed signal.

    Parameters
    ----------
        response: array_like
            response signal (1D array).
        Ts: float, optional
            Sampling time (in nanoseconds). Default is 0.5.
        L_values: List[int], optional
            List of FIR filter lengths to search over. Default is [16, 20, 24, 28, 32, 40, 48].
        lam1_values: List[float], optional
            List of regularization parameters for the identity matrix to search over. Default is [1e-5, 1e-4, 1e-3, 1e-2, 1e-1].
        lam2_values: List[float], optional
            List of regularization parameters for the exponential tail to search over. Default is [1e-5, 1e-4, 1e-3, 1e-2, 1e-1].
    
    Returns
    -------
        best_error: minimum NRMS error found
        best_params: dictionary of optimal parameters (L, lam1, lam2, error, h, reconstructed)
        best_h: best FIR filter coefficients found
        best_reconstructed: reconstructed signal using the best FIR filter
        results: list of dictionaries of all results for each parameter combination
    """
    print("="*70)
    print("OPTIMIZING FIR EXTRACTION PARAMETERS")
    print("="*70)
    print("Searching over L, lam1, lam2 to minimize reconstruction error")
    print("Error = ||response - reconstructed|| / ||response||\n")
    print(f"Signal length: {len(response)} samples")
    print(f"Time span: {(len(response) * Ts):.1f} ns")
    print(f"Sampling time: {Ts:.2f} ns")
    print(f"Sampling rate: {1/Ts:.2f} GS/s\n")

    total_combinations = len(L_values) * len(lam1_values) * len(lam2_values)
    print(f"Total parameter combinations to test: {total_combinations}")
    print(f"L: {L_values}")
    print(f"lam1: {lam1_values}")
    print(f"lam2: {lam2_values}")
    print("\nStarting optimization...\n")

    results = []
    best_error = float('inf')
    best_params = None
    best_h = None
    best_reconstructed = None

    # Ideal signal assumed as a step function
    ideal_response = np.ones(len(response))

    iteration = 0
    for L in L_values:
        for lam1 in lam1_values:
            for lam2 in lam2_values:
                iteration += 1
                try:
                    # Extract forward FIR filter
                    h = fit_fir(response, ideal_response, L=L, Ts=Ts, lam1=lam1, lam2=lam2)
                    h /= np.sum(h)  # Normalize
                    
                    # Reconstruct signal using Toeplitz matrix
                    V = build_toeplitz_matrix(ideal_response, L)
                    reconstructed = V @ h

                    # # Truncate or pad reconstructed to match length
                    # if len(reconstructed) > len(response):
                    #     reconstructed = reconstructed[:len(response)]
                    # elif len(reconstructed) < len(response):
                    #     reconstructed = np.pad(reconstructed, (0, len(response) - len(reconstructed)), 
                    #                           mode='edge')

                    # Compute reconstruction error (NRMS)
                    reconstruction_error = np.linalg.norm(response - reconstructed) / np.linalg.norm(response)
                    
                    # Store results
                    result = {
                        'L': L,
                        'lam1': lam1,
                        'lam2': lam2,
                        'error': reconstruction_error,
                        'h': h.copy(),
                        'reconstructed': reconstructed.copy()
                    }
                    results.append(result)
                    
                    # Track best
                    if reconstruction_error < best_error:
                        best_error = reconstruction_error
                        best_params = result
                        best_h = h.copy()
                        best_reconstructed = reconstructed.copy()
                        
                except Exception as e:
                    print(f"  Warning: Failed for L={L}, lam1={lam1:.0e}, lam2={lam2:.0e}: {e}")
                    continue

    print(f"\n{'='*70}")
    print(f"OPTIMIZATION COMPLETE")
    print(f"{'='*70}")
    print(f"Total combinations tested: {len(results)}")

    return results, best_error, best_params, best_h, best_reconstructed


def analyze_and_plot_fir_fit(
    response: ArrayLike,
    time: ArrayLike,
    Ts: float = 0.5,
    L_values: List[int] = [16, 20, 24, 28, 32, 40, 48],
    lam1_values: List[float] = [1e-5, 1e-4, 1e-3, 1e-2, 1e-1],
    lam2_values: List[float] = [1e-5, 1e-4, 1e-3, 1e-2, 1e-1],
    verbose: bool = True
    ) -> Tuple[np.ndarray, dict, np.ndarray, float]:
    """
    For a given response signal, analyze the FIR filter fit that best reconstructs the response 
    from the ideal step response and plot the results.

    Parameters
    ----------
    response : ArrayLike
        The measured (distorted) response signal to analyze, typically normalized amplitude data.
    time : ArrayLike
        The corresponding time array for the response signal (in ns).
    Ts : float, optional
        The sampling interval (in ns). Default is 0.5.
    L_values : List[int], optional
        The list of FIR filter lengths to search over. Default is [16, 20, 24, 28, 32, 40, 48].
    lam1_values : List[float], optional
        The list of regularization parameters for the identity matrix to search over. Default is [1e-5, 1e-4, 1e-3, 1e-2, 1e-1].
    lam2_values : List[float], optional
        The list of regularization parameters for the exponential tail to search over. Default is [1e-5, 1e-4, 1e-3, 1e-2, 1e-1].
    verbose: bool, optional
        Whether to print verbose output. Default is True.

    Returns
    -------
    best_h : np.ndarray
        The coefficients of the best forward FIR filter found.
    best_params : dict
        Dictionary of the optimal FIR filter hyperparameters.
    best_reconstructed : np.ndarray
        The best reconstructed (filtered) signal from the optimization.
    best_error : float
        Normalized root mean square error (NRMS) for the optimal filter parameters.
    fig : matplotlib.figure.Figure
        The figure object containing the signal reconstruction and FIR coefficients plots.
    """
    results, best_error, best_params, best_h, best_reconstructed = optimize_fir_parameters(
        response, Ts=Ts, L_values=L_values, lam1_values=lam1_values, lam2_values=lam2_values
        )
    if best_params is not None and verbose:
        print(f"\nBEST PARAMETERS:")
        print(f"  L = {best_params['L']}")
        print(f"  lam1 = {best_params['lam1']:.0e}")
        print(f"  lam2 = {best_params['lam2']:.0e}")
        print(f"\nPERFORMANCE:")
        print(f"  Reconstruction error: {best_error:.4e} ({best_error*100:.2f}%)")
        print(f"  Max |h|: {np.max(np.abs(best_h)):.4e}")
        print(f"  h.sum(): {np.sum(best_h):.6f}")
        
        # Visualize best result
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Plot 1: Signal comparison
        ax = axes[0, 0]
        ax.plot(time, response, 'r-', label='Measured (distorted)', linewidth=2, alpha=0.7)
        ax.plot(time, best_reconstructed, 'b--', 
                label=f'Reconstructed (error={best_error:.4e})', linewidth=2)
        ax.set_xlabel('Time (ns)')
        ax.set_ylabel('Amplitude')
        ax.set_title('Best Reconstruction Result')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Plot 2: Residual
        ax = axes[0, 1]
        residual = response - best_reconstructed
        ax.plot(time, residual, 'm-', linewidth=1.5)
        ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)
        ax.fill_between(time, -np.std(residual), np.std(residual), alpha=0.2, color='gray')
        ax.set_xlabel('Time (ns)')
        ax.set_ylabel('Residual')
        ax.set_title(f'Reconstruction Residual (σ={np.std(residual):.4e})')
        ax.grid(True, alpha=0.3)
        
        # Plot 3: Best FIR filter
        ax = axes[1, 0]
        ax.plot(best_h, 'b-o', markersize=4, linewidth=2)
        ax.set_xlabel('Tap Index')
        ax.set_ylabel('Coefficient Value')
        ax.set_title(f'Best Forward FIR (L={best_params["L"]})')
        ax.grid(True, alpha=0.3)
        
        # Plot 4: Error distribution across parameters
        ax = axes[1, 1]
        errors_by_L = {}
        for r in results:
            if r['L'] not in errors_by_L:
                errors_by_L[r['L']] = []
            errors_by_L[r['L']].append(r['error'])
        
        L_sorted = sorted(errors_by_L.keys())
        error_means = [np.mean(errors_by_L[L]) for L in L_sorted]
        error_stds = [np.std(errors_by_L[L]) for L in L_sorted]
        
        ax.errorbar(L_sorted, error_means, yerr=error_stds, fmt='o-', capsize=5, linewidth=2, markersize=6)
        ax.axhline(y=best_error, color='r', linestyle='--', alpha=0.5, label=f'Best: {best_error:.4e}')
        ax.set_xlabel('Filter Length L')
        ax.set_ylabel('Reconstruction Error')
        ax.set_title('Error vs Filter Length')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
        
        # Show top 10 results
        print(f"\n{'='*70}")
        print("TOP 10 PARAMETER COMBINATIONS:")
        print(f"{'='*70}")
        sorted_results = sorted(results, key=lambda x: x['error'])[:10]
        print(f"{'Rank':<6} {'L':<4} {'lam1':<8} {'lam2':<8} {'Error':<12}")
        print("-"*70)
        for i, r in enumerate(sorted_results, 1):
            print(f"{i:<6} {r['L']:<4} {r['lam1']:<8.0e} {r['lam2']:<8.0e} {r['error']:<12.4e}")
        print("="*70)
        
    elif verbose:
        print("ERROR: No valid parameter combinations found!")
        print("Try adjusting parameter ranges or check your data.")

    return best_h, best_params, best_reconstructed, best_error, fig


def invert_fir(
    h: ArrayLike, 
    Ts: float = 0.5, 
    M: Optional[int] = None,
    method: Literal['optimization', 'analytical'] = 'optimization',
    sigma_ns: float = 0.75, 
    lam_smooth: float = 5e-2 ,
    normalize_dc_gain: bool = False
    ) -> np.ndarray:
    """
    Invert a causal FIR filter by finding an inverse causal FIR (possibly smoothed).

    Solves:
        min_{h_inv} || d - (h * h_inv) ||^2 + lam_smooth * || Δ h_inv ||^2

    where:
        - h is the original causal FIR filter coefficients (array-like, length L)
        - h_inv is the inverse FIR filter coefficients (array-like, length M)
        - d is a desired target response (by default, a normalized Gaussian to approximate a causal impulse)
        - * denotes convolution (implemented via Toeplitz matrix multiplication)
        - Δ is the first difference operator (to penalize roughness in h_inv)
        - lam_smooth is the regularization/smoothing parameter

    Parameters
    ----------
    h : array_like
        Original FIR filter coefficients (causal, length L).
    Ts : float, optional
        Sample spacing (default is 0.5).
    M : int, optional
        Length of the inverse FIR filter coefficients to solve for (default is len(h)).
    method : str, optional
        Method to use for inversion ('optimization' or 'analytical').
    sigma_ns : float, optional
        Standard deviation of target Gaussian for delta approximation (default is 1.0).
    lam_smooth : float, optional
        Regularization parameter for first-difference smoothing of h_inv (default is 5e-2).
    normalize_dc_gain: bool, optional
        Whether to normalize the DC gain of the inverse FIR filter to 1. Default is False.
    
    Returns
    -------
    h_inv : ndarray
        FIR inverse coefficients (length M), optionally DC gain-normalized.

    Notes
    -----
    - This routine finds a stable, causal FIR approximate inverse of a given FIR.
    - Regularization improves stability for nearly non-minimum-phase FIRs.
    - The returned inverse may not be exact due to smoothing and length limits.
    """
    h = np.asarray(h, float)
    L = len(h)
    if M is None:
        M = L
    if method == 'optimization':
        # target 'delta'
        t = np.arange(M)*Ts
        d = np.exp(-0.5*(t/(sigma_ns))**2)
        d /= d.sum()  # unit DC gain

        # Build Toeplitz conv matrix H for causal conv(h, h_inv) truncated to M
        H = build_toeplitz_matrix(h, M)[:M, :]

        # First-difference (Sobolev) smoothing
        D = np.eye(M, k=0) - np.eye(M, k=1)
        D = D[:-1, :]  # (M-1) x M

        A = H.T @ H + lam_smooth * (D.T @ D)
        b = H.T @ d
        h_inv = linalg.solve(A, b, assume_a='pos')

        # Optional: normalize composite DC gain to 1
        if normalize_dc_gain:
            gain = (h.sum() * h_inv.sum())
            if gain != 0:
                h_inv /= gain

    elif method == 'analytical':
        h_inv = np.zeros(L)
    
        # First condition
        h_inv[0] = 1 / h[0]
        
        # Recursive computation
        for m in range(1, L):
            s = 0
            for i in range(1, m+1):
                s += h_inv[m-i] * h[i]
            h_inv[m] = -s / h[0]
    
    return h_inv

FIR_filter_coefficient = [[16, 20, 24, 28, 32, 40, 48],[1e-5, 1e-4, 1e-3, 1e-2, 1e-1],[1e-5, 1e-4, 1e-3, 1e-2, 1e-1]]
inverse_FIR_filter_coefficient =[0.75,5e-2,'optimization' ]


def analyze_and_plot_inverse_fir(
    response: ArrayLike,
    time: ArrayLike,
    Ts: float = 0.5,
    L_values: List[int] = FIR_filter_coefficient[0],
    lam1_values: List[float] = FIR_filter_coefficient[1],
    lam2_values: List[float] = FIR_filter_coefficient[2],
    M: Optional[int] = None,
    sigma_ns: float = inverse_FIR_filter_coefficient[0], 
    lam_smooth: float = inverse_FIR_filter_coefficient[1], 
    method: Literal['optimization', 'analytical'] = inverse_FIR_filter_coefficient[2],
    verbose: bool = True
    ) -> np.ndarray:
    """
    Analyze and plot the inverse FIR filter for a given FIR filter.

    Parameters
    ----------
    response: ArrayLike
        The response signal to analyze.
    time: ArrayLike
        The time array for the response signal.
    Ts: float, optional
        The sampling interval (in ns). Default is 0.5.
    L_values: List[int], optional
        The list of FIR filter lengths to search over. Default is [16, 20, 24, 28, 32, 40, 48].
    lam1_values: List[float], optional
        The list of regularization parameters for the identity matrix to search over. Default is [1e-5, 1e-4, 1e-3, 1e-2, 1e-1].
    lam2_values: List[float], optional
        The list of regularization parameters for the exponential tail to search over. Default is [1e-5, 1e-4, 1e-3, 1e-2, 1e-1].
    M: int, optional
        The length of the inverse FIR filter coefficients to solve for (default is len(h)).
    sigma_ns: float, optional
        The standard deviation of the target Gaussian for delta approximation (default is 0.75).
    lam_smooth: float, optional
        The regularization parameter for first-difference smoothing of h_inv (default is 5e-2).
    method: Literal['optimization', 'analytical'], optional
        The method to use for inversion ('optimization' or 'analytical'). Default is 'optimization'.
    verbose: bool, optional
        Whether to print verbose output. Default is True.

    Returns
    -------
    best_h : ndarray
        The best FIR filter coefficients.
    h_inv : ndarray
        The inverse FIR filter coefficients.
    fig_fir_fit : matplotlib.figure.Figure
        The figure object containing the FIR filter fit analysis and optimization plots.
    fig : matplotlib.figure.Figure
        The figure object containing the signal correction analysis and inverse FIR coefficients plots.
    """
    best_h, best_params, best_reconstructed, best_error, fig_fir_fit = analyze_and_plot_fir_fit(
        response=response, 
        time=time, 
        Ts=Ts,
        L_values=L_values,
        lam1_values=lam1_values,
        lam2_values=lam2_values,
        verbose=verbose
        )
    h_inv = invert_fir(
        h=best_h, 
        Ts=Ts, 
        M=M, 
        method=method, 
        sigma_ns=sigma_ns, 
        lam_smooth=lam_smooth
        )
    delta = conv_causal(best_h, h_inv, N=len(best_h))
    ideal_response = np.ones(len(response))
    
    # ===========================================
    # Compute Corrected Signal
    # ===========================================

    # Method 1: Predistort ideal signal, then apply forward distortion
    # (This simulates what would happen in practice)
    L_guard = len(h_inv)
    guard = np.zeros(L_guard)

    # Pad ideal signal
    ideal_padded = np.concatenate([guard, ideal_response, guard])

    # Apply predistortion
    predistorted_padded = conv_causal(ideal_padded, h_inv)

    # Extract central region
    start = L_guard
    end = start + len(ideal_response)
    predistorted_response = predistorted_padded[start:end]

    # Apply forward distortion (simulate what happens in hardware)
    corrected_response = conv_causal(predistorted_response, best_h, N=len(ideal_response))

    # Compute correction error
    correction_error = np.linalg.norm(corrected_response - ideal_response) / np.linalg.norm(ideal_response)
    print(f"Correction error (NRMS): {correction_error:.3e}")

    # Method 2: Apply inverse directly to measured signal
    # (Alternative approach - corrects the measured signal directly)
    distorted_padded = np.concatenate([guard, response, guard])
    corrected_from_measured_padded = conv_causal(distorted_padded, h_inv)
    corrected_from_measured = corrected_from_measured_padded[start:end]

    correction_error_measured = np.linalg.norm(corrected_from_measured - ideal_response) / np.linalg.norm(ideal_response)
    print(f"Correction error (from measured, NRMS): {correction_error_measured:.3e}")

    # ===========================================
    # Visualization
    # ===========================================
    print("\n" + "="*70)
    print("Step 4: Visualization")
    print("="*70)

    fig, axes = plt.subplots(3, 2, figsize=(16, 12))

    # Plot 1: Original signals
    ax = axes[0, 0]
    ax.plot(time, ideal_response, 'g--', label='Ideal Signal', linewidth=2, alpha=0.7)
    ax.plot(time, response, 'r-', label='Distorted Signal', linewidth=2)
    ax.plot(time, best_reconstructed, 'b:', label='Predicted (from FIR)', linewidth=2, alpha=0.7)
    ax.axhline(y=1.001, color='gray', linestyle='--', linewidth=1, alpha=0.7)
    ax.axhline(y=0.999, color='gray', linestyle='--', linewidth=1, alpha=0.7)
    ax.set_ylim([0.95,1.05])
    ax.set_xlabel('Time (ns)')
    ax.set_ylabel('Amplitude')
    ax.set_title('Original Signals and FIR Prediction')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Plot 2: FIR Filters
    ax = axes[0, 1]
    ax.plot(best_h, 'b-o', label='Forward FIR (h)', markersize=4, linewidth=2)
    ax.plot(h_inv, 'r-s', label='Inverse FIR (h_inv)', markersize=4, linewidth=2)
    ax.set_xlabel('Tap Index')
    ax.set_ylabel('Coefficient Value')
    ax.set_title('Extracted FIR Filters')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Plot 3: Predistorted and Corrected Signals
    ax = axes[1, 0]
    ax.plot(time, ideal_response, 'g--', label='Ideal Signal', linewidth=2, alpha=0.7)
    ax.plot(time, predistorted_response, 'c-', label='Predistorted Signal', linewidth=2, alpha=0.7)
    ax.plot(time, corrected_response, 'm-', label='Corrected Signal (sim)', linewidth=2)
    ax.axhline(y=1.001, color='gray', linestyle='--', linewidth=1, alpha=0.7)
    ax.axhline(y=0.999, color='gray', linestyle='--', linewidth=1, alpha=0.7)
    ax.set_ylim([0.95,1.05])
    ax.set_xlabel('Time (ns)')
    ax.set_ylabel('Amplitude')
    ax.set_title('Predistortion and Correction')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Plot 4: Correction Comparison
    ax = axes[1, 1]
    ax.plot(time, ideal_response, 'g--', label='Ideal Signal', linewidth=2, alpha=0.7)
    ax.plot(time, response, 'r-', label='Distorted Signal', linewidth=2, alpha=0.5)
    ax.plot(time, corrected_response, 'm-', label='Corrected (predistort method)', linewidth=2)
    ax.plot(time, corrected_from_measured, 'orange', linestyle='-', 
            label='Corrected (from measured)', linewidth=2, alpha=0.7)
    ax.axhline(y=1.001, color='gray', linestyle='--', linewidth=1, alpha=0.7)
    ax.axhline(y=0.999, color='gray', linestyle='--', linewidth=1, alpha=0.7)
    ax.set_ylim([0.95,1.05])
    ax.set_xlabel('Time (ns)')
    ax.set_ylabel('Amplitude')
    ax.set_title('Correction Comparison')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Plot 5: Error Analysis
    ax = axes[2, 0]
    residual_fit = response - best_reconstructed
    residual_correction = corrected_response - ideal_response
    ax.plot(time, residual_fit, 'b-', label=f'Fit Residual (σ={np.std(residual_fit):.4e})', linewidth=1.5)
    ax.plot(time, residual_correction, 'm-', label=f'Correction Residual (σ={np.std(residual_correction):.4e})', linewidth=1.5)
    ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    ax.set_xlabel('Time (ns)')
    ax.set_ylabel('Residual')
    ax.set_title('Residual Analysis')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Plot 6: h * h_inv (should be close to delta)
    ax = axes[2, 1]
    t_delta = np.arange(len(delta)) * Ts * 1e9  # Convert Ts (seconds) to ns for plotting
    ax.plot(t_delta, delta, 'g-o', markersize=4, linewidth=2)
    ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    ax.set_xlabel('Time (ns)')
    ax.set_ylabel('Amplitude')
    ax.set_title(f'h * h_inv (should approximate δ, peak={np.max(np.abs(delta)):.3e})')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()
    if verbose:
        # ===========================================
        # Summary
        # ===========================================
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Forward FIR (h):")
        print(f"  - Length: {len(best_h)}")
        print(f"  - lam1: {best_params['lam1']:.0e}")
        print(f"  - lam2: {best_params['lam2']:.0e}")
        print(f"  - Sum: {np.sum(best_h):.6f}")
        print(f"  - Max coefficient: {np.max(np.abs(best_h)):.6f}")
        print(f"  - Fit error: {best_error:.3e} ({best_error*100:.2f}%)")

        print(f"\nInverse FIR (h_inv):")
        print(f"  - Length: {len(h_inv)}")
        print(f"  - sigma_ns: {sigma_ns}")
        print(f"  - lam_smooth: {lam_smooth}")
        print(f"  - method: {method}")
        print(f"  - Sum: {np.sum(h_inv):.6f}")
        print(f"  - Max coefficient: {np.max(np.abs(h_inv)):.6f}")

        print(f"\nCorrection Performance:")
        print(f"  - Correction error (predistort method): {correction_error:.3e} ({correction_error*100:.2f}%)")
        print(f"  - Correction error (from measured): {correction_error_measured:.3e} ({correction_error_measured*100:.2f}%)")

        print(f"\nFilter Coefficients:")
        print(f"  Forward FIR (h): {best_h}..." if len(best_h) > 10 else f"  Forward FIR (h): {best_h}")
        print(f"  Inverse FIR (h_inv): {h_inv}..." if len(h_inv) > 10 else f"  Inverse FIR (h_inv): {h_inv}")
        print("="*70)

    return best_h, h_inv, fig_fir_fit, fig

# %% example usage
# load data
with nc.Dataset('/Users/fabioansaloni/Downloads/ds (1).h5', 'r') as f:
    t_data = np.array(f.variables['time'][:])
    y_data = np.squeeze(np.array(f.variables['flux'][:]))

# normalize the response
normalized_response_raw = y_data / y_data[-10:].mean()
# resample the response to 2 GS/s
original_Ts = t_data[1] - t_data[0]
normalized_response_2gsps = resample_to_target_rate(normalized_response_raw, original_Ts, 0.5)
time_2gsps = np.arange(len(normalized_response_2gsps)) * 0.5 + 1
# analyze and plot the forward and inverse FIR filters
h_fir, inv_fir, fig_fir_fit, fig_inv_fir_fit = analyze_and_plot_inverse_fir(
    response=normalized_response_2gsps,
    time=time_2gsps
    )

# how to calculate the predistorted and corrected response
ideal_response = np.ones(len(y_data))
predistorted_response = lfilter(inv_fir, 1, ideal_response)
corrected_response = lfilter(h_fir, 1, predistorted_response)

# feedforward filters to be used in config file
fir_filter = inv_fir.tolist() # or conv_causal(inv_fir, inv_fir_old).tolist() if inv_fir_old already exists
# %%
