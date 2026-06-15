from functools import wraps

def with_app_context(func):
    @wraps(func)
    def _wrapper(app, *args, **kwargs):
        with app.app_context():
            return func(app, *args, **kwargs)
    return _wrapper
