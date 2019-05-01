import os

try:
    import cPickle as pickle
except:
    import pickle

from . import peewee, userdata, signals
from .constants import DB_PATH, DB_PRAGMAS, DB_MAX_INSERTS, DB_TABLENAME, ADDON_DEV
from .util import hash_6

path = os.path.dirname(DB_PATH)
if not os.path.exists(path):
    os.makedirs(path)

db = peewee.SqliteDatabase(DB_PATH, pragmas=DB_PRAGMAS)

if ADDON_DEV:
    import logging
    logger = logging.getLogger('peewee')
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)

class HashField(peewee.TextField):
    def db_value(self, value):
        return hash_6(value)

class PickledField(peewee.BlobField):
    def db_value(self, value):
        if value != None:
            return super(PickledField, self).db_value(pickle.dumps(value, pickle.HIGHEST_PROTOCOL))

    def python_value(self, value):
        if value != None:
            return super(PickledField, self).python_value(pickle.loads(str(value)))

class Model(peewee.Model):
    checksum = ''

    @classmethod
    def get_checksum(cls):
        ctx = db.get_sql_context()
        query = cls._schema._create_table()
        return hash_6([cls.checksum, ctx.sql(query).query()])

    @classmethod
    def delete_where(cls, *args, **kwargs):
        return super(Model, cls).delete().where(*args, **kwargs).execute()

    @classmethod
    def exists_or_false(cls, *args, **kwargs):
        try:
            return cls.select().where(*args, **kwargs).exists()
        except peewee.OperationalError:
            return False

    @classmethod
    def set(cls, *args, **kwargs):
        return super(Model, cls).replace(*args, **kwargs).execute()

    @classmethod
    def table_name(cls):
        return cls._meta.table_name

    @classmethod
    def truncate(cls):
        return super(Model, cls).delete().execute()

    @classmethod
    def replace_many(cls, data):
        with db.atomic():
            for idx in range(0, len(data), DB_MAX_INSERTS):
                super(Model, cls).replace_many(data[idx:idx+DB_MAX_INSERTS]).execute()

    @classmethod
    def insert_many(cls, data):
        with db.atomic():
            for idx in range(0, len(data), DB_MAX_INSERTS):
                super(Model, cls).insert_many(data[idx:idx+DB_MAX_INSERTS]).execute()

    def to_dict(self):
        data = {}

        for field in self._meta.sorted_fields:
            field_data = self.__data__.get(field.name)
            data[field.name] = field_data

        return data

    def __str__(self):
        return str(self.to_dict())

    def __repr__(self):
        return self.__str__

    class Meta:
        database = db
        only_save_dirty = True

class KeyStore(Model):
    key     = peewee.TextField(unique=True)
    value   = peewee.TextField()

    class Meta:
        table_name = DB_TABLENAME

tables = [KeyStore]
def check_tables():
    with db.atomic():
        for table in tables:
            key      = table.table_name()
            checksum = table.get_checksum()

            if KeyStore.exists_or_false(KeyStore.key == key, KeyStore.value == checksum):
                continue

            db.drop_tables([table])
            db.create_tables([table])

            KeyStore.set(key=key, value=checksum)

@signals.on(signals.AFTER_RESET)
def delete():
    close()
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

@signals.on(signals.ON_CLOSE)
def close():
    db.close()

@signals.on(signals.BEFORE_DISPATCH)
def connect():
    db.connect(reuse_if_open=True)
    check_tables()