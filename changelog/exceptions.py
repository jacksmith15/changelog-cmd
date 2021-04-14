class ChangelogError(Exception):
    pass


class ChangelogParseError(ChangelogError):
    pass


class ChangelogValidationError(ChangelogError):
    pass


class ChangelogMissingConfigError(ChangelogError):
    def __init__(self, message: str, field: str = None):
        super().__init__(message)
        self.field = field
