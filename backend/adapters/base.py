class QueryAdapter:
    def execute_scalar(self, sql):
        raise NotImplementedError

    def execute_rows(self, sql):
        raise NotImplementedError
