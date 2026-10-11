class ModelAccessError(RuntimeError):
    """Base error exposed by the model access layer."""


class ModelAccessUnavailableError(ModelAccessError):
    """No usable model service satisfies the request."""


class ModelAccessBusyError(ModelAccessError):
    """Matching services have no free capacity."""


class ModelAccessTimeoutError(ModelAccessError, TimeoutError):
    """Resource acquisition or a model operation exceeded its timeout."""


class ModelAccessResponseError(ModelAccessError):
    """The service response violates the model access contract."""
