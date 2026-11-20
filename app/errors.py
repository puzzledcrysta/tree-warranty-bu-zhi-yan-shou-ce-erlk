class DataError(ValueError):
    def __init__(self, code, detail, status=422):
        super().__init__(detail)
        self.code = code
        self.status = status
