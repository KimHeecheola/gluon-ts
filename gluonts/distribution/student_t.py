# Standard library imports
import math
from typing import Dict, Optional, Tuple

# First-party imports
from gluonts.model.common import Tensor

# Relative imports
from .distribution import (
    Distribution,
    _sample_multiple,
    getF,
    nans_like,
    softplus,
)
from .distribution_output import DistributionOutput


class StudentT(Distribution):
    is_reparameterizable = False

    def __init__(self, mu: Tensor, sigma: Tensor, nu: Tensor, F=None) -> None:
        self.mu = mu
        self.sigma = sigma
        self.nu = nu
        self.F = F if F else getF(mu)

    @property
    def batch_shape(self) -> Tuple:
        return self.mu.shape

    @property
    def event_shape(self) -> Tuple:
        return ()

    @property
    def event_dim(self) -> int:
        return 0

    @property
    def mean(self) -> Tensor:
        return self.F.where(self.nu > 1.0, self.mu, nans_like(self.mu))

    @property
    def stddev(self) -> Tensor:
        F = self.F
        mu, nu, sigma = self.mu, self.nu, self.sigma
        return F.where(nu > 2.0, sigma * F.sqrt(nu / (nu - 2)), nans_like(mu))

    def log_prob(self, x: Tensor) -> Tensor:
        mu, sigma, nu = self.mu, self.sigma, self.nu
        F = self.F

        nup1_half = (nu + 1.0) / 2.0
        part1 = 1.0 / nu * F.square((x - mu) / sigma)
        Z = (
            F.gammaln(nup1_half)
            - F.gammaln(nu / 2.0)
            - 0.5 * F.log(math.pi * nu)
            - F.log(sigma)
        )

        ll = Z - nup1_half * F.log1p(part1)
        return ll

    def sample(self, num_samples: Optional[int] = None) -> Tensor:
        def s(mu: Tensor, sigma: Tensor, nu: Tensor) -> Tensor:
            F = self.F
            gammas = F.sample_gamma(
                alpha=nu / 2.0, beta=2.0 / (nu * F.square(sigma))
            )
            normal = F.sample_normal(mu=mu, sigma=1.0 / F.sqrt(gammas))
            return normal

        return _sample_multiple(
            s,
            mu=self.mu,
            sigma=self.sigma,
            nu=self.nu,
            num_samples=num_samples,
        )


class StudentTOutput(DistributionOutput):
    args_dim: Dict[str, int] = {"mu": 1, "sigma": 1, "nu": 1}
    distr_cls: type = StudentT

    @classmethod
    def domain_map(cls, F, mu, sigma, nu):
        sigma = softplus(F, sigma)
        nu = 2.0 + softplus(F, nu)
        return mu.squeeze(axis=-1), sigma.squeeze(axis=-1), nu.squeeze(axis=-1)

    @property
    def event_shape(self) -> Tuple:
        return ()
