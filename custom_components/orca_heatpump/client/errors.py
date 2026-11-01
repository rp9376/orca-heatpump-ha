"""Errors raised by the Orca client."""


class OrcaError(Exception):
    """Base class of all Orca client errors."""


class OrcaConnectionError(OrcaError):
    """The display could not be reached."""


class OrcaTimeoutError(OrcaConnectionError):
    """The display did not answer in time."""


class OrcaAuthError(OrcaError):
    """The display rejected the username or password."""


class OrcaTooManyUsersError(OrcaError):
    """All of the display's sessions are in use."""


class OrcaProtocolError(OrcaError):
    """The display answered in a way the client does not understand."""


class OrcaSessionExpiredError(OrcaProtocolError):
    """The session token is no longer valid; the client logs in again."""


class OrcaTagError(OrcaError):
    """A tag is unknown to the display or may not be accessed."""


class OrcaWriteError(OrcaError):
    """A write was rejected or did not take effect."""


class OrcaValueError(OrcaError, ValueError):
    """A value is not writable, out of range or of the wrong type."""
