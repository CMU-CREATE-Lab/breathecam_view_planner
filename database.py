import flask_login
from sqlalchemy import Column, Integer, String, Float, Identity, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, scoped_session, sessionmaker
from utils import epsql

engine = epsql.Engine(db_name="breathecam")

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine.engine))
Base = declarative_base()
Base.query = db_session.query_property()

class Panorama(Base):
    __tablename__ = "panoramas"

    id: int = Column(Integer, Identity(always=True), primary_key=True) # autoincrement
    name: str = Column(String, nullable=False)
    image_suffix: str = Column(String, nullable=False)
    image_mime_type: str = Column(String, nullable=False)
    user_id: str = Column(String, ForeignKey("users.id"))
    user = relationship("User")
    viewport_lat: float = Column(Float, default=0)
    viewport_long: float = Column(Float, default=0)
    viewport_name: str = Column(String)
    image_full_width: float = Column(Float)
    image_full_height: float = Column(Float)
    image_cropped_width: float = Column(Float)
    image_cropped_height: float = Column(Float)
    image_cropped_x: float = Column(Float)
    image_cropped_y: float = Column(Float)

    def image_path(self):
        return f"image/{self.id}{self.image_suffix}"

    def image_url(self):
        return f"/{self.image_path()}"
    
    def url(self):
        return f"/p/{self.id}"

    def export_to_client(self):
        return {
            **{k:getattr(self, k) for k in [
                "id", "name", "viewport_lat", "viewport_long", "viewport_name", 
                "image_full_width", "image_full_height", "image_cropped_width", "image_cropped_height", "image_cropped_x", "image_cropped_y"]},
            "user": self.user.export_to_client(),
            "url": self.url(),
            "image_url": self.image_url(),
        }

class WhitelistedEmail(Base):
    __tablename__ = "whitelisted_emails"

    email: str = Column(String, primary_key=True)

class User(Base, flask_login.UserMixin):
    __tablename__ = "users"

    id: str = Column(String, primary_key=True)
    name: str = Column(String, nullable=False)
    email: str = Column(String, nullable=False)

    def export_to_client(self):
        return {k:getattr(self, k) for k in ["id", "name", "email"]}

def init_db(drop_all = False):
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    # import yourapplication.models
    if drop_all:
        Base.metadata.drop_all(engine.engine)
    Base.metadata.create_all(engine.engine)

init_db(drop_all = False)
