from discord import ui, ButtonStyle, Interaction
from global_vars import STFU_USERS, ROLE_COLOR

EMOJI_JOIN = '➕'
EMOJI_LEFT = '🚫'


def get_btn_styles(is_join):
    return {
        'emoji': EMOJI_JOIN if not is_join else EMOJI_LEFT,
        'style': ButtonStyle.green if not is_join else ButtonStyle.blurple
    }


class RolesView(ui.View):
    def __init__(self, guld, user, timeout=300):
        self.guild = guld
        self.user = user
        super().__init__(timeout=timeout)

        for role in filter(
            lambda r: str(r.color) == ROLE_COLOR, self.guild.roles
        ):
            self.add_item(RoleButton(role=role, user=user))

    async def on_timeout(self):
        await self.message.delete()
        return await super().on_timeout()

    async def update_state(self):
        member = await self.guild.fetch_member(self.user.id)

        for child in self.children:
            btn = get_btn_styles(child.custom_id in [str(
                user_role.id) for user_role in member.roles])
            child.emoji = btn.get('emoji')
            child.style = btn.get('style')


class RoleButton(ui.Button):
    def __init__(self, role, user):
        self.role = role
        self.user = user
        btn = get_btn_styles(
            role.id in [user_role.id for user_role in user.roles])

        super().__init__(
            custom_id=str(role.id),
            label=role.name,
            emoji=btn.get('emoji'),
            style=btn.get('style')
        )

    async def callback(self, interaction: Interaction):
        view = self.view

        try:
            if not self.role.id in [user_role.id for user_role in interaction.user.roles]:
                await self.user.add_roles(self.role)
                content = f"You joined '{self.role.name}'"
            else:
                await self.user.remove_roles(self.role)
                content = f"You left '{self.role.name}'"

            await view.update_state()

            await interaction.response.edit_message(content=content, view=view)

        except Exception as e:
            await interaction.response.edit_message(content=f'Try again because we got an error: {e}')


class UserSelect(ui.UserSelect):
    def __init__(self):
        super().__init__(placeholder="Select an user to ask him to shut his mouth up")

    async def callback(self, interaction: Interaction):
        view = self.view

        try:
            user_id = interaction.data.get('values')[0]

            if user_id in STFU_USERS:
                STFU_USERS.remove(user_id)
                content = f'User {user_id} was removed from STFU list'
            else:
                STFU_USERS.append(user_id)
                content = f'User {user_id} was added from STFU list'

            await interaction.response.edit_message(content=f'{content}. Total: {len(STFU_USERS)}')
        except Exception as e:
            await interaction.response.edit_message(content=f'Try again because we got an error: {e}')


class STFUView(ui.View):
    def __init__(self, timeout=30):
        super().__init__(timeout=timeout)
        self.add_item(UserSelect())

    async def on_timeout(self):
        await self.message.delete()
        return await super().on_timeout()


class RoleGreetingModal(ui.Modal, title='Tea bot role options'):
    def __init__(self, bot) -> None:
        super().__init__()
        self.bot = bot

    @property
    def options(self):
        return self.bot.options

    greet_text = ui.TextInput(
        label="Greeting text",
        placeholder='sends with mentioned username into #greet_channel',
    )

    greet_channel = ui.TextInput(
        label='Greeting channel ID')

    greet_text_delay = ui.TextInput(
        label="Greeting text timeout",
        placeholder='after N-seconds the text will be deleted',
        default=60
    )

    report_channel = ui.TextInput(
        label='Report channel ID',
        placeholder="For receiving complaints from users")

    async def on_submit(self, interaction: Interaction) -> None:
        await self.options.put("greet_text", self.greet_text.value)
        await self.options.put("greet_channel", self.greet_channel.value)
        await self.options.put("report_channel", self.report_channel.value)
        await self.options.put("greet_text_delay", self.greet_text_delay.value)
        await interaction.response.send_message('Successfully saved',
                                                ephemeral=True)
