from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    name = Column(String(100), nullable=False)
    type = Column(String(10), nullable=False)
    parent_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    icon = Column(String(50), nullable=True)
    color = Column(String(7), nullable=True)
    is_system = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="categories")
    parent = relationship(
        "Category",
        back_populates="children",
        remote_side=[id]
    )
    children = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan"
    )

    VALID_TYPES = {"income", "expense"}

    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name}, type={self.type})>"
