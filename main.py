import discord
import sys
import logging
import requests

from data.db_session import global_init
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from sdamgia_mod import SdamGIA
from discord.ext import commands
from datetime import datetime, timedelta
from random import choice

from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

from config import settings, tips_oge, tips_ege  # словари с параметрами запуска и советами

from data.db_oge import DB_OGE
from data.db_ege import DB_EGE
from data.remember_check import RExam
from data.stats import Stats

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


# вставить сюда key, после создания базы данных


async def yesnt(message, name, remember=False):  # Проверка ответа (положительный/отрицательный)
    st, exam, subject, numb = All[message.author]
    if st == 0:
        yes = [f'ОГЭ или ЕГЭ, {name}?'] if not remember else \
            [f'Насколько я помню, твой экзамен - {check_RE(str(message.author))[1]}.',
             f'Выбери предмет, с которым тебе нужна помощь, {name}.']
        no = [f'Пока, {name}! Удачи с экзаменами!']
    elif st == 4:
        ExD, ExS = (DB_OGE, sdamoge) if exam == 'огэ' else (DB_EGE, sdamege)
        try:
            id = db_sess.query(ExD.prblm_id).filter(ExD.sbjct == subjects[subject], ExD.numb == numb).first()[0]
        except:
            id = ''
        if id:
            id = choice(id.split('/'))
            prblm = ExS.get_problem_by_id(subjects[subject], id)['condition']
            yes = [prblm['text']]
        else:
            ex = 'o' if exam == 'огэ' else 'e'
            yes = ['Пока что я не смогу дать тебе пример для этого задания самостоятельно.'
                   f' Можешь решить его здесь: https://{subjects[subject]}-{ex}ge.sdamgia.ru/',
                   f'Попробуем другой предмет, {name}?']
        no = [f'Тогда попробуем другой предмет, {name}?']
    elif st == 6:
        yes = [f'Выбери предмет, с которым тебе нужна помощь, {name}.']
        no = [f'Пока, {name}! Удачи с экзаменами!']
    if message.content.lower() in ['да', 'ага', 'давай', 'ок', 'хорошо', 'yes', 'yeah', '+', ]:
        for m in yes:
            await message.channel.send(m)
        if st == 4:
            if not id:
                return -1
            for im in prblm['images']:
                await message.channel.send(file=discord.File(svg_to_png(im)))
            return id
        return 1
    elif message.content.lower() in ['нет', 'не', 'нет, спасибо', 'неа', 'не надо', 'no', '-', ]:
        for m in no:
            await message.channel.send(m)
        return -1
    else:
        await message.channel.send('Не понял ответа. Так да или нет?')
        return 0


def check_RE(user):
    try:
        memb = db_sess.query(RExam).filter(RExam.name == user).first()
        return memb.name, memb.exam, memb.date
    except Exception:
        return '', '', ''


def svg_to_png(img):
    p = requests.get(img)
    rt = 'data/temp_images/'
    nm = 'img.svg'
    out = open(rt + nm, 'wb')
    out.write(p.content)
    out.close()
    renderPM.drawToFile(svg2rlg(rt + nm), rt + f'img.png', fmt='PNG')
    return rt + f'img.png'


@bot.command()
async def menu(ctx):  # Создаем команду menu
    embed = discord.Embed(color=0x45e0ce)  # Создание Embed - красивого меню
    embed.add_field(name='Обо мне', value='''Я - Экзаменатор - дискорд-бот, предназначенный для помощи ученику в 
подготовке к ОГЭ и ЕГЭ.''', inline=False)
    embed.add_field(name='Команды', value='''!menu – представляюсь и рассказываю о своих функциях
!change_exam – меняю экзамен (ОГЭ на ЕГЭ и наоборот)
!change_subject {предмет} – меняю предмет
!reset_exam – забываю вид экзамена
!stats - показываю твою статистику правильности ответов
!reset_stats - забываю твою статистику
!quit – сразу прощаюсь''', inline=False)  # Добавляем контент
    await ctx.send(embed=embed)  # Отправка меню сообщением


@bot.command()
async def change_exam(ctx):
    global All
    exam = All.get(ctx.author, ['e', ''])[1]
    if exam:
        if exam == 'огэ':
            exam = 'егэ'
        else:
            exam = 'огэ'
        await ctx.send(f'Экзамен изменён на {exam}')
        All[ctx.author][1] = exam
        if any(check_RE(str(ctx.author))):
            db_sess.query(RExam).filter(RExam.name == str(ctx.author)).first().exam = exam
            db_sess.commit()
    else:
        await ctx.send(f'Я ещё не знаю твой экзамен, <@{ctx.author.id}>.')


@bot.command()
async def change_subject(ctx, word=''):
    global All
    stage, _, subject, _ = All.get(ctx.author, ['', 0, 0, 0])
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
    if stage == 'e' or not any(check_RE(str(ctx.author))):
        await ctx.send(f'Я ещё не знаю твоего экзамена, <@{ctx.author.id}>')
    elif stage > 1:
        await ctx.send(f'Эта команда должна была использоваться раньше, <@{ctx.author.id}>. '
                       f'Используй !change_exam для смены экзамена.')
    else:
        await ctx.send(f'Теперь я не помню твой экзамен, <@{ctx.author.id}>')
        db_sess.query(RExam).filter(RExam.name == str(ctx.author)).delete()
        db_sess.commit()


@bot.command()
async def stats(ctx):
    stat = db_sess.query(Stats).filter(Stats.name == str(ctx.author)).first()
    if stat:
        await ctx.send(f'У тебя {stat.true} правильных и {stat.false} неправильных ответов, <@{ctx.author.id}>')
    else:
        await ctx.send(f'Ты ещё не решал задания, <@{ctx.author.id}>')


@bot.command()
async def reset_stats(ctx):
    if not db_sess.query(Stats).filter(Stats.name == str(ctx.author)).first():
        await ctx.send(f'Я ещё не знаю твоей статистики, <@{ctx.author.id}>')
    else:
        await ctx.send(f'Теперь я не знаю твоей статистики, <@{ctx.author.id}>')
        db_sess.query(Stats).filter(Stats.name == str(ctx.author)).delete()
        db_sess.commit()


@bot.command()
async def quit(ctx):  # Бот мгновенно прощается
    if All.get(ctx.author, 'ee')[0] in (-1, 'e'):
        await ctx.send(f'Мы ещё не начали общаться, <@{ctx.author.id}>.')
    else:
        await ctx.send(f'Пока, <@{ctx.author.id}>! Удачи с экзаменами!')
        All[ctx.author][0] = -1


# @bot.command()
# async def search(ctx, id):  # поиск задания по id
#     global All
#     try:
#         _, exam, subject, _ = All[ctx.author]
#         ex = sdamoge if exam == 'огэ' else sdamege
#         xz = ex.get_problem_by_id(subject, id)
#         embed = discord.Embed(color=0x45e0ce, title=subject)  # Создание Embed
#         embed.add_field(name=f'''Номер задания: {xz['topic']}''', value=xz['condition']['text'], inline=False)
#         await ctx.send(embed=embed)  # Отправка меню сообщением
#     except:
#         await ctx.send(f'Номер с id:{id} не найден')
#
#
# @bot.command()
# async def test(ctx):
#     global tasks, stage, subject
#     #  subject = str(get_subject(ctx.message.author.id))
#     try:
#         if not len(tasks):
#             await ctx.send('Идёт генерация теста')
#             tasks = sdamgia.get_test_by_id(subject, sdamgia.generate_test(subject))
#             await ctx.send('Тест сгенерирован')
#             # сохранение инфы в бд
#     except Exception:
#         await ctx.send('Ошибка')
#     embed = discord.Embed(color=00000000, title='Задания')  # Создание Embed - красивой менюшки
#     await ctx.send('Отправка сообщения')
#     xz = sdamgia.get_problem_by_id(subject, tasks[stage])
#     embed.add_field(name=f'''Задание: {xz['topic']}''', value=xz['condition']['text'], inline=False)
#     if xz['condition']['images']:
#         embed.add_field(name=f'''Рисунок к заданию: {xz['topic']}''', value=str(xz['condition']['images']))
#     await ctx.send(embed=embed)
#
#
# @bot.command(name='задание')
# async def choice(ctx, number=1):
#     global stage
#     stage = number - 1
#     await test(ctx)
#
#
# @bot.command(name='начать')
# async def test_begin(ctx):
#     import sqlite3
#     sqlite_connection = sqlite3.connect('data.db')
#     cursor = sqlite_connection.cursor()
#     sqlite_insert_query = f"""INSERT INTO users
#                           (user_id, exam, subject,)
#                           VALUES
#                           ('{ctx.message.author.id}', 'oge', 'math');"""
#     count = cursor.execute(sqlite_insert_query)
#     sqlite_connection.commit()
#     cursor.close()
#     user = await bot.fetch_user(user_id=ctx.message.author.id)
#     await user.send('Чтобы начать экзамен введите !test')
#
#
# @bot.command(name='ответ')
# async def show_answer(ctx):
#     global tasks, stage, subject
#     #  subject = str(get_subject(ctx.message.author.id))
#     embed = discord.Embed(color=00000000, title='Ответ')
#     xz = sdamgia.get_problem_by_id(subject, tasks[stage])
#     embed.add_field(name=f'''Ответ к заданию: {xz['topic']}''', value=xz['solution']['text'], inline=False)
#     await ctx.send(embed=embed)
#
#
# @bot.command()
# async def xz(ctx):
#     import io
#     import aiohttp
#
#     async with aiohttp.ClientSession() as session:
#         async with session.get('https://ege.sdamgia.ru/formula/svg/c1/c1bfad09ee23244b2f082cf11d7cc86a.svg') as resp:
#             if resp.status != 200:
#                 return await ctx.send('Не получилось взять изображение')
#             data = io.BytesIO(await resp.read())
#             picture = discord.File(data)
#             await ctx.send(file=picture)
#
#     embed = discord.Embed(color=00000000, title='Помощь')  # Создание Embed - красивой менюшки
#     embed.set_image(url='https://ege.sdamgia.ru/formula/svg/c1/c1bfad09ee23244b2f082cf11d7cc86a.svg')
#     await ctx.send(embed=embed)  # Отправка меню сообщением


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
    if 'Direct Message with ' not in str(message.channel):
        if '<@961286435397304370>' in message.content and (All.get(message.author, 'ee')[0] in (-1, 'e')):
            await message.author.create_dm()
        else:
            return
    if message.author == bot.user:
        return
    if message.author not in All.keys():
        All[message.author] = [-1, '', '', 0]
    All[message.author][1] = check_RE(str(message.author))[1]
    stage, exam, subject, numb = All[message.author]
    name = f'<@{message.author.id}>'
    try:
        if stage == -1:
            stage, exam, subject, numb = -1, '', '', 0
            await message.author.dm_channel.send(f'Привет! Нужна помощь с экзаменом, {name}?')
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
                numb = int(message.content)
                for tip in tips[subject][numb]:
                    await message.channel.send(tip)
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
            if type(a) == str:
                stage = 5
                global id
                id = a
            elif a == -1:
                stage = 6
            raise BaseException
        if stage == 5:
            ExD, ExS = (DB_OGE, sdamoge) if exam == 'огэ' else (DB_EGE, sdamege)
            prblm = ExS.get_problem_by_id(subjects[subject], id)
            ansv = prblm['answer']
            sol = prblm['solution']['text']
            img = prblm['solution']['images']
            if not db_sess.query(Stats).filter(Stats.name == str(message.author)).first():
                stat = Stats()
                stat.name = str(message.author)
                stat.true = 0
                stat.false = 0
                db_sess.add(stat)
                db_sess.commit()
            if message.content.lower() == ansv:
                await message.channel.send(f'Всё верно, {name}! Это {ansv}.')
                db_sess.query(Stats).filter(Stats.name == str(message.author)).first().true += 1
            else:
                await message.channel.send(f'Неверно, {name}! Правильный ответ – {ansv}.')
                db_sess.query(Stats).filter(Stats.name == str(message.author)).first().false += 1
            await message.channel.send(sol)
            for im in img:
                await message.channel.send(file=discord.File(svg_to_png(im)))
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


# global_init("problems.db") # Создать базу данных, после закоменнтировать
bot.run(settings['token'])  # Запуск бота
