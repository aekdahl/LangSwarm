"""
Reflexive Memory System (Dynamic Few-Shot Learning).

A RAG-for-Instructions pipeline that allows a frozen LLM to learn from feedback
by dynamically updating its own system prompt with relevant past lessons.
"""

from .models import Lesson
from .store import LessonStore
from .reflector import ReflectorAgent
from .retriever import LessonRetriever
from .consolidator import LessonConsolidator

__all__ = [
    'Lesson',
    'LessonStore',
    'ReflectorAgent',
    'LessonRetriever',
    'LessonConsolidator'
]
