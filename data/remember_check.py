import sqlalchemy
from datetime import datetime
from .db_session import SqlAlchemyBase


class RExam(SqlAlchemyBase):
    __tablename__ = 'remember_exam'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    date = sqlalchemy.Column(sqlalchemy.DateTime, nullable=True)
    exam = sqlalchemy.Column(sqlalchemy.String, nullable=True)