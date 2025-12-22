"""Mock dependencies for local development without AWS setup."""

# Mock Strands SDK
def tool(func):
    """Mock tool decorator for local development."""
    return func

# Mock AWS Lambda Powertools
class MockLogger:
    def __init__(self, **kwargs):
        self.child = kwargs.get('child', False)
    
    def info(self, msg, **kwargs):
        print(f"INFO: {msg}")
    
    def error(self, msg, **kwargs):
        print(f"ERROR: {msg}")
    
    def warning(self, msg, **kwargs):
        print(f"WARNING: {msg}")
    
    def exception(self, msg, **kwargs):
        print(f"EXCEPTION: {msg}")
    
    def inject_lambda_context(self, **kwargs):
        def decorator(func):
            return func
        return decorator


class MockTracer:
    def __init__(self, **kwargs):
        pass
    
    def capture_method(self, func):
        return func
    
    def capture_lambda_handler(self, func):
        return func


class MockMetrics:
    def __init__(self, **kwargs):
        pass
    
    def add_dimension(self, **kwargs):
        pass
    
    def add_metric(self, **kwargs):
        pass
    
    def log_metrics(self, **kwargs):
        def decorator(func):
            return func
        return decorator


# Mock Lambda Context
class LambdaContext:
    pass