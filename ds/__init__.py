try:
    from rich import traceback
except ImportError:
    pass
else:
    traceback.install()
    traceback.pretty.install()