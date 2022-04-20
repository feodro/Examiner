import sqlalchemy
from .db_session import SqlAlchemyBase


class DB_OGE(SqlAlchemyBase):
    __tablename__ = 'oge_problems'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    sbjct = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    prblm_id = sqlalchemy.Column(sqlalchemy.String, nullable=True)