# Third-party imports
import mxnet as mx
import numpy as np


class MetricAttentiveScheduler(mx.lr_scheduler.LRScheduler):
    """
    This scheduler decreases the learning rate based on the value of some
    validation metric to be optimized (maximized or minimized). The value
    of such metric is provided by calling the `step` method on the scheduler.
    A `patience` parameter must be provided, and the scheduler will reduce
    the learning rate if no improvement in the metric is done before
    `patience` observations of the metric.

    Examples:

        `patience = 0`: learning rate will decrease at every call to
        `step`, regardless of the metric value

        `patience = 1`: learning rate is reduced as soon `step` is called
        with a metric value which does not improve over the best encountered

        `patience = 10`: learning rate is reduced if no improvement in the
        metric is recorded in 10 successive calls to `step`
    """

    def __init__(
        self,
        objective: str,
        patience: int,
        base_lr: float = 0.01,
        decay_factor: float = 0.5,
        min_lr: float = 0.0,
    ) -> None:
        """

        :param objective: string, can either be `"min"` or `"max"`
        :param patience:  int, the patience to observe before reducing the
            learning rate
        :param base_lr: initial learning rate to be used
        :param decay_factor: factor by which to decrease the learning rate
        :param min_lr: lower bound for the learning rate, learning rate will
            never go below `min_lr`
        """
        assert base_lr > 0, f"base_lr should be positive, got {base_lr}"

        assert (
            0 < decay_factor < 1
        ), f"decay_factor factor should be between 0 and 1, got {decay_factor}"

        assert patience >= 0, f"patience should be nonnegative, got {patience}"

        assert objective in [
            "min",
            "max",
        ], f"objective should be 'min' or 'max', got {objective}"

        super(MetricAttentiveScheduler, self).__init__(base_lr=base_lr)

        self.decay_factor = decay_factor
        self.patience = patience
        self.objective = objective
        self.min_lr = min_lr
        self.best_metric = np.Inf if objective == "min" else -np.Inf
        self.prev_change = 0
        self.epoch_no = 0
        self.curr_lr = None

    def __call__(self, num_update: int) -> float:
        if self.curr_lr is None:
            self.curr_lr = self.base_lr
        assert self.curr_lr is not None

        return self.curr_lr

    def step(self, metric_value: float) -> None:
        """
        Inform the scheduler of the new value of the metric that is being
        optimized. This method should be invoked at regular intervals (e.g.
        at the end of every epoch, after computing a validation score).

        :param metric_value: value of the metric that is being optimized.
        """
        if self.curr_lr is None:
            self.curr_lr = self.base_lr
        assert self.curr_lr is not None

        metric_improved = (
            self.objective == "min" and metric_value < self.best_metric
        ) or (self.objective == "max" and metric_value > self.best_metric)

        if metric_improved:
            self.best_metric = metric_value
            self.prev_change = self.epoch_no

        if self.epoch_no - self.prev_change >= self.patience:
            self.curr_lr = max(self.min_lr, self.decay_factor * self.curr_lr)
            self.prev_change = self.epoch_no

        self.epoch_no += 1
