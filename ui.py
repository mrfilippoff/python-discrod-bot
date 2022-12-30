from discord import ui, ButtonStyle, Interaction
from discord.utils import get

class RolesView(ui.View):
    def __init__(self,  roles, user, timeout=15):
        super().__init__(timeout=timeout)

        for role in roles:
            self.add_item(RoleButton(role=role, user=user))

    async def on_timeout(self) -> None:
        return await super().on_timeout()

class RoleButton(ui.Button):
    def __init__(self, role, user):
        self.role=role
        self.user=user
        self.is_join=role.id in [user_role.id for user_role in user.roles]
        super().__init__(label=f'{role.name} [{len(role.members)}]', emoji='➕' if not self.is_join else '🚫', style=ButtonStyle.green if not self.is_join else ButtonStyle.blurple )


    async def callback(self, interaction):
        if interaction.is_expired():
            await interaction.response.send_message(content=f'Oops. Too late', ephemeral=True)
            return

        try:
            if not self.role.id in [user_role.id for user_role in self.user.roles]:
                await self.user.add_roles(self.role)
                text_result = f"You added '{self.role.name}'"
            else:
                await self.user.remove_roles(self.role)
                text_result = f"You removed '{self.role.name}'"


            print(f'message.id {self.view.message.id}')
            #await self.view.message.edit(content=text_result, view=self.view)
            await interaction.response.edit_message(content=text_result, view=self.view)
            # await interaction.response.defer()

        except Exception as e:
            await interaction.response.edit_message(content=f'Ooops. Error: {e}')

        #await interaction.response.send_message(content=f"Actions with the role '{self.role.name}'", view=EditRoleButtons(role=self.role, ctx=self.ctx, is_join=self.is_join), ephemeral=True)


class EditRoleButtons(ui.View):
    def __init__(self, *, role, ctx, is_join):
        self.role = role
        self.ctx=ctx
        super().__init__()

    @property
    def is_join(self):
        return self.role.id in [_r.id for _r in self.ctx.message.author.roles]
    
    @ui.button(label="Add Role", style=ButtonStyle.primary)
    async def join_button(self, interaction:Interaction, button:ui.Button):
        try:
            await self.ctx.message.author.add_roles(self.role)
            await interaction.response.edit_message(content=f"You've added '{self.role.name}'")
        except Exception as e:
            await interaction.response.edit_message(content=f'Ooops. Error: {e}')

    @ui.button(label="Remove Role", style=ButtonStyle.danger)
    async def leave_button(self, interaction:Interaction, button:ui.Button):
        try:
            await self.ctx.message.author.remove_roles(self.role)
            await interaction.response.edit_message(content=f"You've removed '{self.role.name}'")
        except Exception as e:
            await interaction.response.send_message(content=f'Oops. Error: {e}', ephemeral=True)
