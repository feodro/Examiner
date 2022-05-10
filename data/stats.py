# Столбец бд, в котором хранится количество правильных и неправильных ответов пользователя
import sqlalchemy
from db_session import SqlAlchemyBase


class Stats(SqlAlchemyBase):
    __tablename__ = 'stats'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    true = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    false = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)