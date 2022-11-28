#%%

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base, relationship

import epsql

engine = epsql.Engine(db_name="breathecam")

Base = declarative_base()

class User(Base):
    __tablename__ = "user_account"

    id = Column(Integer, primary_key=True)
    name = Column(String(30))
    fullname = Column(String)

    addresses = relationship(
        "Address", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"User(id={self.id!r}, name={self.name!r}, fullname={self.fullname!r})"



# %%
declarative_base.