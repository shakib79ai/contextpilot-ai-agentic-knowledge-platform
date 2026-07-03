import enum


class UserRole(str, enum.Enum):
    admin = "admin"
    reviewer = "reviewer"
    member = "member"


class DocumentStatus(str, enum.Enum):
    pending = "pending"
    indexing = "indexing"
    indexed = "indexed"
    failed = "failed"


class AnswerStatus(str, enum.Enum):
    auto_answered = "auto_answered"
    low_confidence = "low_confidence"
    escalated = "escalated"
    reviewed_approved = "reviewed_approved"
    reviewed_edited = "reviewed_edited"
    reviewed_rejected = "reviewed_rejected"


class FeedbackKind(str, enum.Enum):
    thumbs_up = "thumbs_up"
    thumbs_down = "thumbs_down"
    reviewer_approve = "reviewer_approve"
    reviewer_edit = "reviewer_edit"
    reviewer_reject = "reviewer_reject"


class ReviewStatus(str, enum.Enum):
    pending = "pending"
    in_review = "in_review"
    resolved = "resolved"


class ReviewPriority(str, enum.Enum):
    low = "low"
    normal = "normal"
    high = "high"


class KnowledgeUpdateStatus(str, enum.Enum):
    proposed = "proposed"
    approved = "approved"
    rejected = "rejected"
    applied = "applied"


class MessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"
