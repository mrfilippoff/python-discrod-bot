import peewee
import json

dbhandle = peewee.SqliteDatabase(
    'data.db'
)


class BaseModel(peewee.Model):
    class Meta:
        database = dbhandle


class JSONField(peewee.TextField):
    def db_value(self, value):
        return json.dumps(value)

    def python_value(self, value):
        if value is not None:
            return json.loads(value)

