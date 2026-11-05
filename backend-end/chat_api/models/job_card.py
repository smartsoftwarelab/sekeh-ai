import json
from datetime import datetime, timezone
from ..extensions import db


class JobCard(db.Model):
    __tablename__ = "job_cards"

    id = db.Column(db.BigInteger, primary_key=True)

    message_id = db.Column(
        db.BigInteger,
        db.ForeignKey("messages.message_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    cards_json = db.Column(db.JSON, nullable=False)

    is_marked = db.Column(db.Boolean, default=False, nullable=False, index=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    message = db.relationship("Message", backref="job_cards")

    def to_dict(self):
        return {
            "message_id": self.message_id,
            "is_marked": self.is_marked,
            "items": self.cards_json,
        }