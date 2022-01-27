class EmptyInstanceHeadAccess(ValueError, IndexError):
    def __init__(self, *args, hint: str='', **kwargs):
        super().__init__(*args, **kwargs)
        self.hint = f'\nHint: {hint}' * bool(hint)

class InvalidIntegerSliceError(ValueError, TypeError):
    pass