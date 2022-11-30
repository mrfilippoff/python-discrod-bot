## Deploy bot (python 3.8 or higher)

1.Set up project's venv

`python3 -m venv venv`

2.Activate the venv

`source ./venv/bin/activate`

3.Install requirements

`pip install -r req2.txt`

4.Create .env based on env.example.txt (test bot TOKEN)

5.Run bot

`python bot.py`

### voice_client.py uses discord-ext-audiorec (build ffi.pyd for win64 from https://github.com/Shirataki2/discord-ext-audiorec)
