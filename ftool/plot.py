from __future__ import division

import numpy as np
import scipy.stats as stats

def poisson_errors(N, kind, confidence=0.6827):
    alpha = 1 - confidence
    upper = np.zeros(len(N))
    lower = np.zeros(len(N))
    if kind == 'gamma':
        lower = stats.gamma.ppf(alpha / 2, N)
        upper = stats.gamma.ppf(1 - alpha / 2, N + 1)
    elif kind == 'sqrt':
        err = np.sqrt(N)
        lower = N - err
        upper = N + err
    else:
        raise ValueError('Unknown errorbar kind: {}'.format(kind))

    lower[N==0] = 0
    return N - lower, upper - N

def hist_points(namedhist, density=False, yerr="gamma", **kwargs):
    import matplotlib.pyplot as plt
    name, h, bins = namedhist

    width  = np.diff(bins)
    center = bins[:-1] + width/2.0
    area   = np.sum(h * width)

    if isinstance(yerr, str):
        yerr = poisson_errors(h, yerr)
    xerr = width / 2

    if density:
        h = h / area
        yerr = yerr / area
        area = 1.

    if not 'color' in kwargs:
        kwargs['color'] = 'black'

    if not 'fmt' in kwargs:
        kwargs['fmt'] = 'o'

    if not 'lw' in kwargs:
        kwargs['lw'] = 2.0

    kwargs["capsize"] = 0#None
    kwargs["capthick"] = None

    plt.errorbar(center, h, xerr=xerr, yerr=yerr, **kwargs)

    return center, (yerr[0], h, yerr[1]), area


def hist_steps(namedhist, density=False, **kwargs):
    import matplotlib.pyplot as plt
    name, h, bins = namedhist

    width  = np.diff(bins)
    center = bins[:-1] + width/2.0
    area   = np.sum(h * width)

    if density:
        h = h / area
        area = 1.

    if not 'lw' in kwargs:
        kwargs['lw'] = 2.0

    if not 'histtype' in kwargs:
        kwargs["histtype"] = "step"

    plt.hist(center, bins=bins, weights=h, **kwargs)
    return center, h, area
