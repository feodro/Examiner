import discord
import sys
from sdamgia import SdamGIA
from discord.ext import commands
from config import settings  # словарь с параметрами запуска
bot = commands.Bot(command_prefix=settings['prefix'])  # инциализация бота
sdamgia = SdamGIA()
from help import subjects
subject = 'math'
tasks = []
exam = 'ege'


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
    global exam
    if exam == 'ege':
        exam = 'oge'
        await ctx.send('Тип экзамена - огэ')
    else:
        exam = 'ege'
        await ctx.send('Тип экзамена - егэ')


@bot.command()
async def change_subject(ctx, word=''):
    global subject, subjects
    if len(word):
        if word in subjects.keys():
            subject = subjects[word]
        else:
            await ctx.send(f'Предмет {word} не найден ошибка')
            embed = discord.Embed(color=00000000, title='Помощь')  # Создание Embed - красивой менюшки
            embed.add_field(name='Предметы:',
                            value='; '.join(subjects.keys()))
            await ctx.send(embed=embed)  # Отправка меню сообщением
    else:
        await ctx.send('Введите название предмета')


@bot.command()
async def reset_exam(ctx):
    global tasks
    tasks = []
    await ctx.send('Вариант сброшен')


@bot.command()
async def quit(ctx):  # выключение бота
    await ctx.send('GG')
    sys.exit()


@bot.command()
async def search(ctx, id):  # поиск по id
    global subject
    try:
        xz = sdamgia.get_problem_by_id(subject, id)
        embed = discord.Embed(color=00000000, title=subject)  # Создание Embed
        embed.add_field(name=f'''Номер задания: {xz['topic']}''', value=xz['condition']['text'], inline=False)
        await ctx.send(embed=embed)  # Отправка меню сообщением
    except:
        await ctx.send(f'Номер с id:{id} не найден')


@bot.command()
async def test(ctx):
    global tasks, subject
    if len(tasks):
        pass
    else:
        await ctx.send('Идёт генерация теста')
        tasks = generate_test(subject)
        await ctx.send('Тест сгенерирован')
    embed = discord.Embed(color=00000000, title='Задания')  # Создание Embed - красивой менюшки
    await ctx.send('Отправка сообщения')
    for i in tasks[:5]:
        xz = sdamgia.get_problem_by_id(subject, i)
        embed.add_field(name=f'''Задание: {xz['topic']}''', value=xz['condition']['text'], inline=False)
        if xz['condition']['images']:
            embed.add_field(name=f'''Рисунок к заданию: {xz['topic']}''', value=str(xz['condition']['images']))
    await ctx.send(embed=embed)


@bot.command()
async def gen_test(ctx):
    global tasks, subject
    tasks = generate_test(subject)
    await ctx.send('Тест сгенерирован')


@bot.command()
async def farther(ctx):
    pass


def generate_test(sub):
    return sdamgia.get_test_by_id(sub, sdamgia.generate_test(sub))


bot.run(settings['token'])  # Запуск бота