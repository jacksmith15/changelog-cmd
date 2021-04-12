class ChangelogError(Exception):
    pass


class ChangelogParseError(ChangelogError):
    pass


class ChangelogValidationError(ChangelogError):
    pass
