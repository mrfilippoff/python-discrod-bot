import peewee
import datetime
from db.base import BaseModel, JSONField


class UserEmoji(BaseModel):
    user_id = peewee.IntegerField(unique=True, primary_key=True)
    user_data = JSONField()


class UserEmojis(BaseModel):
    user = peewee.ForeignKeyField(
        UserEmoji,
        on_delete='cascade',
        on_update='cascade',
        backref='set_to_me'
    )
    by_user = peewee.ForeignKeyField(
        UserEmoji,
        on_delete='cascade',
        on_update='cascade',
        backref='set_by_me'
    )
    emoji = peewee.CharField()
    created_at = peewee.DateTimeField(default=datetime.datetime.now())
    message_id = peewee.IntegerField()

