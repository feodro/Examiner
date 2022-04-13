import discord
import sys
from sdamgia import SdamGIA
from discord.ext import commands
from config import settings  # словарь с параметрами запуска
bot = commands.Bot(command_prefix=settings['prefix'])  # инциализация бота
sdamgia = SdamGIA()


@bot.event
async def on_ready():  # Event on_ready активируется когда бот готов к использованию
    print('Bot connected successfully!')


@bot.command()
async def menu(ctx):  # Создаем комманду menu
    embed = discord.Embed(color=0xff9900, title='Помощь')  # Создание Embed - красивой менюшки
    embed.add_field(name='Команды', value='''!menu или помощь – бот представляется и рассказывает о своих функциях
!change_exam или смена экзамена – меняет экзамен (ОГЭ на ЕГЭ и наоборот)
!change_subject или смена предмета – меняет предмет
!reset_exam или сброс – забывает вид экзамена
!quit – бот сразу прощается''', inline=True)  # Добавляем контент
    await ctx.send(embed=embed)  # Отправка меню сообщением


@bot.command()
async def change_exam(ctx):
    await ctx.send('В разработке')


@bot.command()
async def change_subject(ctx, word=''):
    if len(word):
        if word.lower() == 'русский':
            await ctx.send(sdamgia.get_problem_by_id('rus', 1001)['condition']['text'])
        elif word.lower() == 'математика':
            await ctx.send(sdamgia.get_problem_by_id('math', 1001)['condition']['text'])
        else:
            await ctx.send('Такой предмет не найден ошибка 404')
    else:
        await ctx.send('Введите название предмета')


@bot.command()
async def reset_exam(ctx):
    await ctx.send('В разработке')


@bot.command()
async def quit(ctx):  # выключение бота
    await ctx.send('GG')
    sys.exit()


bot.run(settings['token'])  # Запуск бота