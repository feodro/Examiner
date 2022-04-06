import discord

TOKEN = "OTYxMjg2NDM1Mzk3"+"MzA0Mzcw.Yk2xwg.f0KoRk6E"+"g7ZUwPHjXAZci7VgTOA"

SUBJECTS = ['здесь будут предметы',
            'русск',
            'математик',
            'английск',
            'информатик']
stage = -1
exam = ''
subject = ''
numb = 0


class BotClient(discord.Client):
    async def on_ready(self):
        print(f'{self.user} подключился к Discord!')

    async def on_message(self, message):
        global stage
        global exam
        global subject
        global numb
        if message.author == self.user:
            return
        if stage == -1:
            await message.channel.send('Привет! Нужна помощь с экзаменом?')
            stage = 0
            return
        if not stage:
            if 'да' in message.content.lower():
                await message.channel.send('ОГЭ или ЕГЭ?')
                stage = 1
            elif 'нет' in message.content.lower():
                await message.channel.send('Пока! Удачи с экзаменами!')
                stage = -1
            else:
                await message.channel.send('Не понял ответа. Так да или нет?')
            return
        if stage == 1:
            if "огэ" in message.content.lower():
                exam = 'огэ'
                await message.channel.send('Выбери предмет, с которым тебе нужна помощь.')
                stage = 2
            elif "егэ" in message.content.lower():
                exam = 'егэ'
                await message.channel.send('Выбери предмет, с которым тебе нужна помощь.')
                stage = 2
            else:
                await message.channel.send('Не понял ответа. Так какой экзамен?')
            return
        if stage == 2:
            if any(i in message.content.lower() for i in SUBJECTS):
                await message.channel.send('Какое задание?')
                subject = message.content.lower()
                stage = 3
            else:
                await message.channel.send('Я пока не знаю такого предмета. Может другой?')
            return
        if stage == 3:
            await message.channel.send('Пока что я не могу помочь тебе с этим заданием.')
            stage = -1
            return


client = BotClient()
client.run(TOKEN)
