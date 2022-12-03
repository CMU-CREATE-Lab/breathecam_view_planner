#%%

from sqlalchemy import Column, Integer, String, Identity
from sqlalchemy.orm import declarative_base, relationship

from utils import epsql

engine = epsql.Engine(db_name="breathecam")

Base = declarative_base()

class User(Base):
    __tablename__ = "user_account"

    id: int = Column(Integer, Identity(always=True), primary_key=True)
    name: str = Column(String(30))
    fullname = Column(String)

    #addresses = relationship(
    #    "Address", back_populates="user", cascade="all, delete-orphan"
    #)

    def __repr__(self):
        return f"User(id={self.id!r}, name={self.name!r}, fullname={self.fullname!r})"



#%%
u = User()

# %%
u
# %%
u = User(name="hithere")
# %%
u
# %%
print(u.name)
# %%
u.id