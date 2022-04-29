import discord
from sdamgia import SdamGIA
from discord.ext import commands
from config import settings, subjects  # словарь с параметрами запуска
bot = commands.Bot(command_prefix=settings['prefix'])  # инциализация бота
sdamgia = SdamGIA()
tasks = []
stage = 0
subject = 'math'


@bot.event
async def on_ready():  # Event on_ready активируется когда бот готов к использованию
    print('Bot connected successfully!')


@bot.command(name='помощь')
async def menu(ctx):  # Создаем комманду menu
    embed = discord.Embed(color=00000000, title='Помощь')  # Создание Embed - красивой менюшки
    embed.add_field(name='!menu',
                    value='''помощь – бот представляется и рассказывает о своих функциях''', inline=False)
    embed.add_field(name='!change_exam', value='''смена экзамена – меняет экзамен (ОГЭ на ЕГЭ и наоборот)''', inline=False)
    embed.add_field(name='!change_subject', value='''смена предмета – меняет предмет''', inline=False)
    embed.add_field(name='!reset_exam', value='''сброс – забывает вид экзамена''', inline=False)
    embed.add_field(name='!quit', value='''бот сразу прощается''', inline=False)
    await ctx.send(embed=embed)  # Отправка меню сообщением


@bot.command()
async def change_exam(ctx):
    import sqlite3
    con = sqlite3.connect('data.db')
    cur = con.cursor()
    exam = cur.execute(f'''SELECT exam FROM users WHERE id = '{ctx.message.author.id}')''').fetchone()
    cur.close()
    if exam == 'ege':
        await save_type_exam('oge', ctx.message.author.id)
        await ctx.send('Тип экзамена - огэ')
    else:
        await save_type_exam('ege', ctx.message.author.id)
        await ctx.send('Тип экзамена - егэ')


@bot.command()
async def change_subject(ctx, word=''):
    global subjects, subject
    #  subject = str(get_subject(ctx.message.author.id))
    if len(word):
        if word in subjects.keys():
            subject = subjects[word]
            await ctx.send(f'Текущий предмет: {word}')
            #  import sqlite3
            #  sqlite_connection = sqlite3.connect('data.db')
            #  cursor = sqlite_connection.cursor()
            #  sqlite_insert_query = f"""INSERT INTO users
            #                        (subject)
            #                        VALUES
            #                        ('{subjects[word]}') WHERE id = '{ctx.message.author.id}')"""
            #  count = cursor.execute(sqlite_insert_query)
            #  sqlite_connection.commit()
            #  cursor.close()
        else:
            await ctx.send(f'Предмет {word} не найден ошибка')
            embed = discord.Embed(color=00000000, title='Помощь')  # Создание Embed - красивой менюшки
            embed.add_field(name='Предметы:',
                            value='; '.join(subjects.keys()))
            await ctx.send(embed=embed)  # Отправка меню сообщением
    else:
        await ctx.send('Введите название предмета')


@bot.command(name='сброс')
async def reset_exam(ctx):
    global tasks
    tasks = []
    await ctx.send('Вариант сброшен')


@bot.command()
async def quit(ctx):  # выход с сервера
    await ctx.send('До свидания.')
    await bot.get_guild(ctx.message.guild.id).leave()
    print('Bot has left server')


@bot.command(name='поиск')
async def search(ctx, id):  # поиск задания по id
    global subject
    try:
        #  subject = str(get_subject(ctx.message.author.id))
        #  print(subject)
        xz = sdamgia.get_problem_by_id(subject, id)
        embed = discord.Embed(color=00000000, title=subject)  # Создание Embed
        embed.add_field(name=f'''Номер задания: {xz['topic']}''', value=xz['condition']['text'], inline=False)
        await ctx.send(embed=embed)  # Отправка меню сообщением
    except:
        await ctx.send(f'Номер с id:{id} не найден')


@bot.command()
async def test(ctx):
    global tasks, stage, subject
    #  subject = str(get_subject(ctx.message.author.id))
    try:
        if not len(tasks):
            await ctx.send('Идёт генерация теста')
            tasks = sdamgia.get_test_by_id(subject, sdamgia.generate_test(subject))
            await ctx.send('Тест сгенерирован')
            # сохранение инфы в бд
    except Exception:
        await ctx.send('Неизвестная ошибка')
    embed = discord.Embed(color=00000000, title='Задания')  # Создание Embed - красивой менюшки
    await ctx.send('Отправка сообщения')
    xz = sdamgia.get_problem_by_id(subject, tasks[stage])
    embed.add_field(name=f'''Задание: {xz['topic']}''', value=xz['condition']['text'], inline=False)
    if xz['condition']['images']:
        embed.add_field(name=f'''Рисунок к заданию: {xz['topic']}''', value=str(xz['condition']['images']))
    await ctx.send(embed=embed)


@bot.command(name='следующее')
async def farther(ctx):
    global stage
    stage += 1
    await test(ctx)


@bot.command(name='предыдущее')
async def previous(ctx):
    global stage
    stage -= 1
    await test(ctx)


@bot.command(name='задание')
async def choice(ctx, number=1):
    global stage
    stage = number - 1
    await test(ctx)


@bot.command(name='начать')
async def test_begin(ctx):
    import sqlite3
    sqlite_connection = sqlite3.connect('data.db')
    cursor = sqlite_connection.cursor()
    sqlite_insert_query = f"""INSERT INTO users
                          (user_id, exam, subject,)
                          VALUES
                          ('{ctx.message.author.id}', 'oge', 'math');"""
    count = cursor.execute(sqlite_insert_query)
    sqlite_connection.commit()
    cursor.close()
    user = await bot.fetch_user(user_id=ctx.message.author.id)
    await user.send('Чтобы начать экзамен введите !test')


@bot.command(name='ответ')
async def show_answer(ctx):
    global tasks, stage, subject
    #  subject = str(get_subject(ctx.message.author.id))
    embed = discord.Embed(color=00000000, title='Ответ')
    xz = sdamgia.get_problem_by_id(subject, tasks[stage])
    embed.add_field(name=f'''Ответ к заданию: {xz['topic']}''', value=xz['solution']['text'], inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def xz(ctx):
    import io
    import aiohttp

    async with aiohttp.ClientSession() as session:
        async with session.get('https://ege.sdamgia.ru/formula/svg/c1/c1bfad09ee23244b2f082cf11d7cc86a.svg') as resp:
            if resp.status != 200:
                return await ctx.send('Не получилось взять изображение')
            data = io.BytesIO(await resp.read())
            picture = discord.File(data)
            await ctx.send(file=picture)

    embed = discord.Embed(color=00000000, title='Помощь')  # Создание Embed - красивой менюшки
    embed.set_image(url='https://ege.sdamgia.ru/formula/svg/c1/c1bfad09ee23244b2f082cf11d7cc86a.svg')
    await ctx.send(embed=embed)  # Отправка меню сообщением


async def save_type_exam(name, id):
    import sqlite3
    sqlite_connection = sqlite3.connect('data.db')
    cursor = sqlite_connection.cursor()
    exam = cursor.execute(f"""INSERT INTO users
                      (exam)
                      VALUES
                      ('{name}') WHERE id = '{id}'""").fetchone()
    sqlite_connection.commit()
    cursor.close()


async def get_subject(id):
    global subject
    #  import sqlite3
    #  con = sqlite3.connect('data.db')
    #  cur = con.cursor()
    #  subject = cur.execute(f'''SELECT subject FROM users WHERE id = '{id}')''').fetchone()
    #  cur.close()
    return subject


bot.run(settings['token'])  # Запуск бота