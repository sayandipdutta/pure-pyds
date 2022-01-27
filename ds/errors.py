class EmptyInstanceHeadAccess(AttributeError, IndexError):
    def __init__(self, *args, hint: str='', **kwargs):
        super().__init__(*args, **kwargs)
        self.hint = f'\nHint: {hint}' * bool(hint)
        self

class InvalidIntegerSliceError(ValueError, TypeError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.args and isinstance(self.args[0], Exception):
            self.original_exception = self.args[0].__class__
        else:
            self.original_exception = None