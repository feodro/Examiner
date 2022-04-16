import discord
import sys
import logging
from sdamgia import SdamGIA
from discord.ext import commands
from config import settings  # словарь с параметрами запуска

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

bot = commands.Bot(command_prefix=settings['prefix'])  # инициализация бота
sdamgia = SdamGIA()

SUBJECTS = {'русский': 1,  # предметы и id советов
            'математика': 2,
            'информатика': 3,
            'физика': 4,
            'химия': 5,
            'биология': 6,
            'география': 7,
            'история': 8,
            'обществознание': 9,
            'английский': 10}

stage = -1
exam = ''
subject = ''
numb = 0


def yesnt(message, st):  # Проверка ответа (положительный/отрицательный)
    if st == 0:
        yes = 'ОГЭ или ЕГЭ?'
        no = 'Пока! Удачи с экзаменами!'
    elif st == 4:
        yes = 'Zadacha'
        no = 'Тогда попробуем другой предмет?'
    elif st == 6:
        yes = 'Выбери предмет, с которым тебе нужна помощь.'
        no = 'Пока! Удачи с экзаменами!'
    if message in ['да', 'ага', 'давай', 'ок', 'хорошо', 'yes', 'yeah', '+', ]:
        return yes, 1
    elif message in ['нет', 'не', 'нет, спасибо', 'неа', 'не надо', 'no', '-', ]:
        return no, -1
    else:
        return 'Не понял ответа. Так да или нет?', 0


@bot.command()
async def menu(ctx):  # Создаем команду menu
    embed = discord.Embed(color=0x45e0ce)  # Создание Embed - красивой менюшки
    embed.add_field(name='Обо мне', value='''Я - Экзаменатор - дискорд-бот, предназначенный для помощи ученику в 
подготовке к ОГЭ и ЕГЭ.''', inline=False)
    embed.add_field(name='Команды', value='''!menu – представляюсь и рассказываю о своих функциях
!change_exam – меняю экзамен (ОГЭ на ЕГЭ и наоборот)
!change_subject – меняю предмет
!reset_exam – забываю вид экзамена
!quit – сразу прощаюсь''', inline=False)  # Добавляем контент
    await ctx.send(embed=embed)  # Отправка меню сообщением


@bot.command()
async def change_exam(ctx):
    global exam
    exam1 = exam
    if exam1:
        if exam1 == 'огэ':
            exam = 'егэ'
        else:
            exam = 'огэ'
        await ctx.send(f'{exam1}->{exam}')
    else:
        await ctx.send('Бот ещё не знает экзамен')


@bot.command()
async def change_subject(ctx, word=''):
    if len(word):
        if word.lower() == 'русский':
            await ctx.send(sdamgia.get_problem_by_id('rus', 1001)['condition']['text'])
        elif word.lower() == 'математика':
            await ctx.send(sdamgia.get_problem_by_id('math', 1001)['condition']['text'])
        else:
            await ctx.send('Такой предмет не найден')
    else:
        await ctx.send('Вы не ввели название предмета')


@bot.command()
async def reset_exam(ctx):
    await ctx.send('В разработке')


@bot.command()
async def quit(ctx):  # Бот мгновенно прощается
    global stage
    await ctx.send('Пока! Удачи с экзаменами!')
    stage = -1


@bot.event
async def on_ready():
    logger.info(f'{bot.user} подключился к Discord!')
    serv = f'{bot.user} может помочь с подготовкой к экзаменам на ' \
           f'серверах: ' if bot.guilds else f'{bot.user} не сможет помочь с подготовкой к экзаменам на серверах.'
    logger.info(serv)
    for guild in bot.guilds:
        logger.info(f'- {guild.name} (id: {guild.id})')


@bot.event
async def on_message(message):
    global stage, exam, subject, numb
    if str(message.content)[0] == '!':
        await bot.process_commands(message)
        return
    if 'Direct Message with ' not in str(message.channel) and stage == -1:
        if '<@&961337063322583144>' not in message.content:
            return
    if message.author == bot.user:
        return
    if stage == -1:
        await message.channel.send('Привет! Нужна помощь с экзаменом?')
        stage = 0
        return
    if not stage:
        m, a = yesnt(message.content.lower(), 0)
        await message.channel.send(m)
        if a == 1:
            stage = 1
        elif a == -1:
            stage = -1
        return
    if stage == 1:
        if "огэ" in message.content.lower():
            exam = 'огэ'
        elif "егэ" in message.content.lower():
            exam = 'егэ'
        else:
            await message.channel.send('Не понял ответа. Так какой экзамен?')
            return
        await message.channel.send('Выбери предмет, с которым тебе нужна помощь.')
        stage = 2
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
        if not message.content.isdigit():
            await message.channel.send('Это не задание!')
        elif 'условие':
            numb = int(message.content)
            await message.channel.send(f'Здесь должен быть совет по номеру'
                                       f' {numb} предмета {subject}, {exam}')
            # await message.channel.send(file=discord.File(''))
            await message.channel.send('Проверим знания на практике?')
            stage = 4
        else:
            await message.channel.send('Пока что я не могу помочь тебе с этим заданием.')
        return
    if stage == 4:
        m, a = yesnt(message.content.lower(), 4)
        await message.channel.send(m)
        if a == 1:
            stage = 5
        elif a == -1:
            stage = 6
        return
    if stage == 5:
        if message.content.lower() == 'otvet':
            await message.channel.send(f'Всё верно! Это {"otvet"}')
        else:
            await message.channel.send(f'Неверно! Правильный ответ – {"otvet"}')
        await message.channel.send(f'reshenie')
        await message.channel.send('Попробуем ещё?')
        stage = 4
        return
    if stage == 6:
        m, a = yesnt(message.content.lower(), 6)
        await message.channel.send(m)
        if a == 1:
            stage = 2
        elif a == -1:
            stage = -1
        return


bot.run(settings['token'])  # Запуск бота
