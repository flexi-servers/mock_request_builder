from datetime import datetime

from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text
from sqlalchemy.orm import declarative_base

RevisionBase = declarative_base()

class Revision(RevisionBase):
    __tablename__ = "revisions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String(45), nullable=False)

    tablename = Column(String(45), nullable=False)
    row_id = Column(Integer, nullable=False)

    type = Column(String(45), nullable=False)
    key = Column(String(45), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)

    created_at = Column(Date, nullable=True)
    updated_ad = Column(Date, default=datetime.utcnow, nullable=True)

    # other stuff
    exclude_keys = []