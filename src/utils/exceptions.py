class CrudError(Exception):  # Renamed from CrudException to follow naming convention
    pass


class CrudIntegrityError(CrudError):
    pass


class CrudUniqueValidationError(CrudIntegrityError):
    pass


class AgentRunFailedError(Exception):
    pass
