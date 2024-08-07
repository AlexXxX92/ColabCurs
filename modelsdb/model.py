import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class VK_ID(Base):
    __tablename__ = 'vk_id'

    id_user = sq.Column(sq.Integer, primary_key=True)
    id_user_vk = sq.Column(sq.BigInteger,  nullable=False, unique=True)


class Favorits(Base):
    __tablename__ = 'favorits'
    id_favorit = sq.Column(sq.Integer, primary_key=True)
    id_favorit_vk = sq.Column(sq.Integer, nullable=False, unique=True)


class VK_Favorit(Base):
    __tablename__ = 'vk_favorit'
    id_user_vk = sq.Column(sq.Integer, sq.ForeignKey('vk_id.id_user'), primary_key=True)
    id_favorit_vk = sq.Column(sq.Integer, sq.ForeignKey('favorits.id_favorit'), primary_key=True)

    id_user = relationship(VK_ID, backref='vk_id')
    id_favorit = relationship(Favorits, backref='favorits')


def create_tables(engine):
    Base.metadata.create_all(engine)

def drop_tables(engine):
    Base.metadata.drop_all(engine)