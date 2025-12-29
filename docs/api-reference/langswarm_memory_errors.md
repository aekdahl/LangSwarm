# Langswarm_Memory Errors API

**Module:** `langswarm_memory.errors`

## Overview

Error handling for LangSwarm Memory

Provides clear, actionable error messages for memory-related issues.

## Table of Contents

### Classes
- [EmbeddingError](#embeddingerror)
- [LangSwarmMemoryError](#langswarmmemoryerror)
- [MemoryBackendError](#memorybackenderror)
- [MemoryConfigurationError](#memoryconfigurationerror)
- [MemoryStorageError](#memorystorageerror)
- [VectorSearchError](#vectorsearcherror)

## Classes

### EmbeddingError

```python
class EmbeddingError(LangSwarmMemoryError)
```

Raised when embedding operations fail


### LangSwarmMemoryError

```python
class LangSwarmMemoryError(Exception)
```

Base error for langswarm_memory operations


### MemoryBackendError

```python
class MemoryBackendError(LangSwarmMemoryError)
```

Raised when backend operations fail


### MemoryConfigurationError

```python
class MemoryConfigurationError(LangSwarmMemoryError)
```

Raised when configuration is invalid


### MemoryStorageError

```python
class MemoryStorageError(LangSwarmMemoryError)
```

Raised when memory storage operations fail


### VectorSearchError

```python
class VectorSearchError(LangSwarmMemoryError)
```

Raised when vector search operations fail

