class EmptyInstanceHeadAccess(AttributeError, IndexError):
    def __init__(self, *args, hint: str='', **kwargs):
        super().__init__(*args, **kwargs)
        self.hint = f'\nHint: {hint}' * bool(hint)

    def __str__(self):
        return (super().__str__() + self.hint)
        
class InvalidIntegerSliceError(ValueError, TypeError):
    def __init__(self, *args, orig=None, **kwargs):
        if isinstance(orig, Exception):
            super().__init__(*args, orig, **kwargs)
        self.original_exception = orig.__class__

    def __str__(self):
        return (
            super().__str__() 
            + f"\nOrig: {self.original_exception}" 
            * (self.original_exception is not None)
        )