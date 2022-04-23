import discord
import sys
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sdamgia_mod import SdamGIA
from discord.ext import commands
from datetime import datetime, timedelta

from config import settings, tips_oge, tips_ege  # словарь с параметрами запуска

from data.db_oge import DB_OGE
from data.db_ege import DB_EGE
from data.remember_check import RExam

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

bot = commands.Bot(command_prefix=settings['prefix'])  # инициализация бота
sdamoge = SdamGIA('o')  # Инициализации sdamgia-api
sdamege = SdamGIA('e')
engine = create_engine("sqlite:///db/problems.db?check_same_thread=False")  # Инициализация сессии БД
db_sess = Session(bind=engine)

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

All = {}


# oge = DB_OGE()
# oge.sbjct = 'rus'
# oge.prblm_id = '30485'
# ege = DB_EGE()
# ege.sbjct = 'rus'
# ege.prblm_id = ''
# db_sess.add(oge)
# db_sess.add(ege)
# db_sess.commit()


async def yesnt(message, name, remember=False):  # Проверка ответа (положительный/отрицательный)
    st, exam, subject, numb = All[message.author]
    if st == 0:
        yes = [f'ОГЭ или ЕГЭ, {name}?'] if not remember else \
            [f'Насколько я помню, твой экзамен - {exm}.', f'Выбери предмет, с которым тебе нужна помощь, {name}.']
        no = [f'Пока, {name}! Удачи с экзаменами!']
    elif st == 4:
        yes = [sdamoge.get_problem_by_id(subjects[subject], 393952)] if exam == 'огэ' \
            else [sdamege.get_problem_by_id(subjects[subject], 26578)['condition']['text']]
        no = [f'Тогда попробуем другой предмет, {name}?']
    elif st == 6:
        yes = [f'Выбери предмет, с которым тебе нужна помощь, {name}.']
        no = [f'Пока, {name}! Удачи с экзаменами!']
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


def check_RE(user):
    nam = list(db_sess.query(RExam.name).filter(RExam.name == user))[0][0]
    exm = list(db_sess.query(RExam.exam).filter(RExam.name == user))[0][0]
    date = list(db_sess.query(RExam.date).filter(RExam.name == user))[0][0]
    return nam, exm, date


@bot.command()
async def menu(ctx):  # Создаем команду menu
    embed = discord.Embed(color=0x45e0ce)  # Создание Embed - красивого меню
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
    global All
    exam = All.get(ctx.author, ['lmao', ''])[1]
    if exam:
        if exam == 'огэ':
            exam = 'егэ'
        else:
            exam = 'огэ'
        await ctx.send(f'Экзамен изменён на {exam}')
        All[ctx.author][1] = exam
        if any(check_RE(str(ctx.author))):
            db_sess.query(RExam.exam).filter(RExam.name == str(ctx.author)).first().eaxm = exam
    else:
        await ctx.send(f'Я ещё не знаю твой экзамен, <@{ctx.author.id}>.')


@bot.command()
async def change_subject(ctx, word=''):
    global All
    stage, _, subject, _ = All.get(ctx.author, ['ору', 0, 0, 0])
    if not word:
        await ctx.send(f'Ты не указал предмет, <@{ctx.author.id}>')
    elif not subject:
        await ctx.send(f'Я не знаю твой изначальный предмет, <@{ctx.author.id}>.')
    elif word in subjects.keys():
        await ctx.send(f'Предмет изменён на {word}. Какое задание, <@{ctx.author.id}>?')
        All[ctx.author][0], All[ctx.author][2] = 3, word
    else:
        await ctx.send(f'Это не предмет, <@{ctx.author.id}>!')


@bot.command()
async def reset_exam(ctx):
    stage, exam, _, _ = All.get(ctx.author, ['e', '', '', ''])
    if stage > 2:
        await ctx.send(f'Эта команда должна была использоваться раньше, <@{ctx.author.id}>. '
                       f'Используй !change_exam для смены экзамена.')
    elif stage == 'e' or not any(check_RE(str(ctx.author))):
        await ctx.send(f'Я ещё не знаю твоего экзамена, <@{ctx.author.id}>')
    else:
        await ctx.send(f'Теперь я не помню твой экзамен, <@{ctx.author.id}>')
        db_sess.query(RExam).filter(RExam.name == str(ctx.author)).delete()
        db_sess.commit()


@bot.command()
async def quit(ctx):  # Бот мгновенно прощается
    if All.get(ctx.author, 'ee')[0] in (-1, 'e'):
        await ctx.send(f'Мы ещё не начали общаться, <@{ctx.author.id}>.')
    else:
        await ctx.send(f'Пока, <@{ctx.author.id}>! Удачи с экзаменами!')
        All[ctx.author][0] = -1


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
    global All
    logger.info(f'{message.author.name} говорит: {message.content}')
    if str(message.content)[0] == '!':
        await bot.process_commands(message)
        return
    if 'Direct Message with ' not in str(message.channel) and (All.get(message.author, 'sryimnew')[0] in (-1, 's')):
        if '<@961286435397304370>' not in message.content:
            return
    if message.author == bot.user:
        return
    if message.author not in All.keys():
        All[message.author] = [-1, '', '', 0]
    stage, exam, subject, numb = All[message.author]
    name = f'<@{message.author.id}>'
    try:
        if stage == -1:
            await message.channel.send(f'Привет! Нужна помощь с экзаменом, {name}?')
            stage = 0
            raise BaseException
        if not stage:
            nam, exam, date = check_RE(str(message.author))
            remember = nam and (datetime.now() - date) < timedelta(days=2) if date else False
            a = await yesnt(message, name, remember)
            if a == 1:
                if remember:
                    stage = 2
                else:
                    stage = 1
                    if nam:
                        exam = ''
                        db_sess.query(RExam).filter(RExam.name == str(message.author)).delete()
                        db_sess.commit()
            elif a == -1:
                stage = -1
            raise BaseException
        if stage == 1:
            if "огэ" in message.content.lower():
                exam = 'огэ'
            elif "егэ" in message.content.lower():
                exam = 'егэ'
            else:
                await message.channel.send(f'Не понял ответа. Так какой экзамен, {name}?')
                raise BaseException
            remember_exam = RExam()
            remember_exam.name = str(message.author)
            remember_exam.exam = exam
            remember_exam.date = datetime.now()
            db_sess.add(remember_exam)
            db_sess.commit()
            await message.channel.send(f'Выбери предмет, с которым тебе нужна помощь, {name}.')
            stage = 2
            raise BaseException
        if stage == 2:
            if any(i in message.content.lower() for i in subjects):
                await message.channel.send(f'Какое задание, {name}?')
                subject = message.content.lower()
                stage = 3
            else:
                await message.channel.send(f'Я пока не знаю такого предмета, {name}. Может другой?')
            raise BaseException
        if stage == 3:
            if not message.content.isdigit():
                m = f'Такого задания нет, {name}! Выбери другое.' if message.content[0] == '-' \
                    else f'Это не задание, {name}! Выбери другое.'
                await message.channel.send(m)
                raise BaseException
            tips = tips_oge if exam == 'огэ' else tips_ege
            if int(message.content) in tips[subject].keys():
                print(2)
                numb = int(message.content)
                for tip in tips[subject][numb]:
                    await message.channel.send(tip)
                    # await message.channel.send(file=discord.File(''))
                if tips[subject][numb]:
                    await message.channel.send(f'Проверим знания на практике, {name}?')
                else:
                    await message.channel.send(f'Пока что я не могу помочь тебе с этим заданием, {name}.')
                    await message.channel.send(f'Попрактикуемся в таком случае на примерах?')
                stage = 4
            else:
                await message.channel.send(f'Такого задания нет, {name}! Выбери другое.')
            raise BaseException
        if stage == 4:
            a = await yesnt(message, name)
            if a == 1:
                stage = 5
            elif a == -1:
                stage = 6
            raise BaseException
        if stage == 5:
            if message.content.lower() == 'otvet':
                await message.channel.send(f'Всё верно, {name}! Это {"otvet"}')
            else:
                await message.channel.send(f'Неверно, {name}! Правильный ответ – {"otvet"}')
            await message.channel.send(f'reshenie')
            await message.channel.send(f'Попробуем ещё, {name}?')
            stage = 4
            raise BaseException
        if stage == 6:
            a = await yesnt(message, name)
            if a == 1:
                stage = 2
            elif a == -1:
                stage = -1
            raise BaseException
    except BaseException:
        All[message.author] = [stage, exam, subject, numb]
        return


bot.run(settings['token'])  # Запуск бота
