import peewee
from discord import Guild as discordGuild,  Role as DiscordRole, Permissions
from db.base import BaseModel, dbhandle


def check_permissions_with_bots(permissions: Permissions, guild: discordGuild):
    me = guild.me
    return not permissions.is_superset(me.top_role.permissions)


class Guild(BaseModel):
    id = peewee.IntegerField(unique=True, primary_key=True)
    name = peewee.CharField()
    data = peewee.BareField(null=True)

    @staticmethod
    def get_guild(role_id):
        return Guild.get(Guild.id == role_id)


class Role(BaseModel):
    guild = peewee.ForeignKeyField(
        Guild,
        on_delete='cascade',
        on_update='cascade',
        backref='roles'
    )
    id = peewee.IntegerField(null=False, unique=True, primary_key=True)
    name = peewee.CharField()
    is_managed = peewee.BooleanField(default=False)
    is_available = peewee.BooleanField(default=False)
    created_at = peewee.DateTimeField()
    data = peewee.BareField(null=True)
    emoji = peewee.CharField(null=True)

    class Meta:
        indexes = (
            (('emoji', 'id', 'name'), True),
        )

    @staticmethod
    def mapper(discord_duild: discordGuild, guild: Guild, role: DiscordRole):
        return {
            'guild': guild,
            'id': role.id,
            'name': role.name,
            'is_managed': role.managed,
            'is_available': check_permissions_with_bots(role.permissions, discord_duild),
            'created_at': role.created_at
        }

    @staticmethod
    def get_role(role_id):
        return Role.get(Role.id == role_id)

    @staticmethod
    @dbhandle.atomic()
    def insert_many_roles(discord_guild: discordGuild, guild: Guild):
        for role in discord_guild.roles:
            try:
                Role.get_or_create_role(discord_guild, guild, role)
            except Exception as e:
                print('error', e)

    @staticmethod
    @dbhandle.atomic()
    def get_or_create_role(discord_duild: discordGuild, guild: Guild, role: DiscordRole):
        fields = Role.mapper(discord_duild, guild, role)

        try:
            role = Role.get_by_id(fields['id'])
        except Role.DoesNotExist:
            role = Role.insert(
                **fields
            ).execute()
        return role

    @staticmethod
    @dbhandle.atomic()
    def update_role(discord_guild: discordGuild, guild: Guild, role: DiscordRole):
        fields = Role.mapper(discord_guild, guild, role)
        query = Role.update(**fields).where(Role.id == fields['id'])
        query.execute()
