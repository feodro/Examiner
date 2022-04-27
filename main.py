import discord
import sys
import logging
from data import db_session
from sdamgia_mod import SdamGIA
from discord.ext import commands
from config import settings  # словарь с параметрами запуска
from data.db_oge import DB_OGE
from data.db_ege import DB_EGE
from data.remember_check import RExam

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

bot = commands.Bot(command_prefix=settings['prefix'])  # инициализация бота
sdamoge = SdamGIA('o')
sdamege = SdamGIA('e')

subjects = {'русский': 'rus',  # предметы и их id
            'математика': 'math',
            'информатика': 'inf',
            'физика': 'phys',
            'химия': 'chem',
            'биология': 'bio',
            'география': 'geo',
            'история': 'hist',
            'обществознание': 'soc',
            'английский': 'en'}

stage = -1
exam = ''
subject = ''
numb = 0
remember_exam = False


# oge = DB_OGE()
# ege = DB_EGE()
# oge.sbjct = 'rus'
# oge.prblm_id = '30485'
# ege.sbjct = 'rus'
# ege.prblm_id = ''
# db_sess = db_session.create_session()
# db_sess.add(oge)
# db_sess.add(ege)
# db_sess.commit()


async def yesnt(message, st):  # Проверка ответа (положительный/отрицательный)
    if st == 0:
        yes = ['ОГЭ или ЕГЭ?'] if not remember_exam else ['Выбери предмет, с которым тебе нужна помощь.']
        no = ['Пока! Удачи с экзаменами!']
    elif st == 4:
        yes = [sdamoge.get_problem_by_id(subjects[subject], 393952)] if exam == 'огэ'\
            else [sdamege.get_problem_by_id(subjects[subject], 26578)['condition']['text']]
        no = ['Тогда попробуем другой предмет?']
    elif st == 6:
        yes = ['Выбери предмет, с которым тебе нужна помощь.']
        no = ['Пока! Удачи с экзаменами!']
    if message.content.lower() in ['да', 'ага', 'давай', 'ок', 'хорошо', 'yes', 'yeah', '+', ]:
        for m in yes:
            await message.channel.send(m)
        return 1
    elif message.content.lower() in ['нет', 'не', 'нет, спасибо', 'неа', 'не надо', 'no', '-', ]:
        for m in no:
            await message.channel.send(m)
        return -1
    else:
        await message.channel.send('Не понял ответа. Так да или нет?')
        return 0


@bot.command()
async def menu(ctx):  # Создаем команду menu
    embed = discord.Embed(color=0x45e0ce)  # Создание Embed - красивой менюшки
    embed.add_field(name='Обо мне', value='''Я - Экзаменатор - дискорд-бот, предназначенный для помощи ученику в 
подготовке к ОГЭ и ЕГЭ.''', inline=False)
    embed.add_field(name='Команды', value='''!menu – представляюсь и рассказываю о своих функциях
!change_exam – меняю экзамен (ОГЭ на ЕГЭ и наоборот)
!change_subject {предмет} – меняю предмет
!reset_exam – забываю вид экзамена
!quit – сразу прощаюсь''', inline=False)  # Добавляем контент
    await ctx.send(embed=embed)  # Отправка меню сообщением


@bot.command()
async def change_exam(ctx):
    global exam
    if exam:
        if exam == 'огэ':
            exam = 'егэ'
        else:
            exam = 'огэ'
        await ctx.send(f'Экзамен изменён на {exam}')
    else:
        await ctx.send('Бот ещё не знает экзамен')


@bot.command()
async def change_subject(ctx, word=''):
    global subject, stage
    if word in subjects.keys():
        await ctx.send(f'Предмет изменён на {word}. Какое задание?')
        subject = word
        stage = 3
    else:
        await ctx.send('Это не предмет!')


@bot.command()
async def reset_exam(ctx):
    global remember_exam, exam, stage
    if stage < 2:
        m = f'Теперь я не помню экзамен {ctx.author.name}' \
            if remember_exam else f'Я ещё не знаю экзамена {ctx.author.name}'
        remember_exam = False
        exam = ''
        await ctx.send(m)
    else:
        await ctx.send('Эта команда должна была использоваться раньше. Используй !change_exam для смены экзамена.')


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
    global stage, exam, subject, numb, remember_exam
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
        a = await yesnt(message, 0)
        if a == 1:
            stage = 1 if not remember_exam else 2
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
        remember_exam = True
        stage = 2
        return
    if stage == 2:
        if any(i in message.content.lower() for i in subjects):
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
        a = await yesnt(message, 4)
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
        a = await yesnt(message, 6)
        if a == 1:
            stage = 2
        elif a == -1:
            stage = -1
        return


db_session.global_init("db/problems.db")
# bot.run(settings['token'])  # Запуск бота
