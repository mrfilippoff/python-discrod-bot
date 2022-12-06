## Deploy teabot (python 3.8 or higher)

#### 1.Creation of virtual environment.

Install `python3.8-venv` (if you use `python 3.8`) in your system and then:

`python3 -m venv venv`

#### 2.Activate the venv

`source ./venv/bin/activate`

#### 3.Install requirements

it uses `torch` and `numpy` modules because the bot'll talk when it will be move to a high-power server so i did not remove chat feature from the code

```
sudo apt-get install python3-dev
pip install -r requirements.txt
```

#### 4.Create .env based on `env.example.txt` file (test bot TOKEN)

Teabot is tied to the TEA PARTY server and to the channels, so you need to refactor the bot code so that it works either anywhere or only on your server

#### 5.Run bot

`python3 bot.py`

#### 6. Init

If bot has ran at first time on your server have to run `+init` command in the chat
