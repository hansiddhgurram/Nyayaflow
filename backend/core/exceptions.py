"""Custom exceptions."""

class NyayaFlowException(Exception):
    """Base exception."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class EvidenceProcessingError(NyayaFlowException):
    def __init__(self, message: str = "Failed to process evidence"):
        super().__init__(message, status_code=500)


class LLMError(NyayaFlowException):
    def __init__(self, message: str = "LLM inference failed"):
        super().__init__(message, status_code=503)


class RAGError(NyayaFlowException):
    def __init__(self, message: str = "Legal retrieval failed"):
        super().__init__(message, status_code=503)
