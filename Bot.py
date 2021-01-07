#!bin/bash

import telebot
from telebot import types
import pickle, re
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import date, datetime
import logging
import os, sys

with open('api_token.txt', 'r') as  file:
    token = file.read().strip()
bot = telebot.TeleBot(token, parse_mode=None)

logging.basicConfig(level=logging.INFO)

# include all categories
with open('categories.pickle', 'rb') as file:
    categories = pickle.load(file)

zero_expenses = dict()
for c in categories:
    zero_expenses[c] = []

try:
    with open('expenses.pickle', 'rb') as file:
        expenses = pickle.load(file)
except EOFError:
    expenses = zero_expenses

current_cat = None


@bot.message_handler(commands=['help'])
def welcome_message(message):
    bot.reply_to(message, '''Welcome to CurBot. I respond to these commands:
    /start - start using the bot
    /help - obtain a list of commands
    /info - learn more about CurBot
    ''')


@bot.message_handler(commands=['info'])
def introduce_bot(message):
    bot.reply_to(message, 'I am a bot that tracks any kind of expenses you have on a monthly basis.' \
        ' Also, you can obtain an overview of all your expenses sorted by category.' \
        ' The expenses can be reset.'
    )
    

@bot.message_handler(commands=['new'])
def add_new_category(message):
    '''add a new category to track expenses'''
    # when adding a new category via the bot, make sure to include an inline keyboard for it in use_bot
    bot.reply_to(message, 'Which category would you like to add?')

    @bot.message_handler(regexp='[a-zA-Z]{3,}')
    def add_category(message):
        cat = message.text.lower()
        global categories, expenses
        categories.append(cat)
        expenses[cat] = list()
        with open('categories.pickle', 'wb') as f:
            pickle.dump(categories, f)
        bot.reply_to(message, f'{cat} has been added.')


@bot.message_handler(commands=['start', 'add'])
def use_bot(message):
    '''
    use inline keyboard to add expenses or reset them;
    when a new category is added, it needs to be added to be accessed in the bot chat
    '''
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    # include all categories
    a = types.InlineKeyboardButton(text="Household", callback_data="household")
    b = types.InlineKeyboardButton(text="Hobby", callback_data="hobby")
    c = types.InlineKeyboardButton(text="Education", callback_data="education")
    d = types.InlineKeyboardButton(text="Clothes", callback_data="clothes")
    e = types.InlineKeyboardButton(text="Books", callback_data="books")
    f = types.InlineKeyboardButton(text="RESET ALL", callback_data="reset")
    keyboard.add(a, b, c, d, e, f)
    bot.reply_to(message, "What kind of expense do you want to add?", reply_markup=keyboard)

    
    @bot.callback_query_handler(func=lambda m: True)
    def parse_callback(call):
        ''''''
        global expenses
        cat = call.data

        if cat in categories:
            global current_cat
            current_cat = cat
            print('cat check')
            bot.reply_to(call.message, 'Please specify the amount of money.')

        elif cat == 'reset':
            bot.reply_to(call.message, 'Are you sure you want to reset all expenses?')
            reset_bot()

        else:
            bot.reply_to(call.message, 'Please use the inline keyboard or a command.')

        print(expenses)


def reset_bot():
    '''
    makes a back-up of current expenses and then resets them
    '''
    no_answer = True
    while no_answer:
        @bot.message_handler(content_types=['text'])
        def double_check(message):
            nonlocal no_answer
            global expenses
            if message.text in ('yes', 'Yes'):
                # save current expenses to file
                with open(f'expenses_state_{date.today()}.pickle', 'wb') as file:
                    pickle.dump(expenses, file)
                # reset expenses
                expenses = zero_expenses
                with open('expenses.pickle', 'wb') as file:
                    pickle.dump(zero_expenses, file)
                bot.reply_to(message, 'Expenses succesfully reset.')
                no_answer = False
                logging.info(f'Expenses reset at {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}.')
            elif message.text in ('no', 'No'):
                bot.reply_to(call.message, 'Command aborted. Expenses remain unchanged.')
                no_answer = False


@bot.message_handler(commands=['reset'])
def reset_expenses(message):
    '''reset expenses (alternative to inline keyboard)'''
    bot.reply_to(message, 'Are you sure you want to reset all expenses?')
    reset_bot()


@bot.message_handler(regexp='[0-9]+([.,][0-9]+)?')
def get_expense(message):
    '''any number types into the chat will be considered as expense
    as long as there is a current_cat(egory)'''
    global current_cat
    if current_cat:
        exp = float(message.text)
        print(exp)
        expenses[current_cat].append(exp)
        bot.reply_to(message, f'{exp}€ were added to {current_cat}.')
        print(expenses)
        current_cat = None
    else:
        bot.reply_to(message, 'Please specify a category using /start or /add.')


@bot.message_handler(commands=['del'])
def del_expense(message):
    '''Deletes most recently added expense for 
    a requested category'''
    bot.reply_to(message, 'Name the category of the expense you want to delete.')
    @bot.message_handler(content_types=['text'], func=lambda m: m.text in categories)
    def del_category_expense(message):
        global expenses
        cat = message.text.lower()
        try:
            del expenses[cat][-1]
            print(expenses)
            bot.reply_to(message, f'Last expense added to {cat} was successfully deleted.')
        except IndexError:
            bot.reply_to(message, f'No expenses in {cat}.')



@bot.message_handler(commands=['plot'])
def plot_expenses(message):
    exps, cats = list(), list()
    for cat in categories:
        if expenses[cat]:
            exps.append(sum(expenses[cat]))
            cats.append(cat)

    # set style for bar chart
    sns.set_style('darkgrid')
    sns.set_palette('crest')

    sns.barplot(cats, exps)

    # save plot to file and send to chat
    plt.savefig('plot.png')
    bot.send_photo(message.chat.id, photo=open('plot.png', 'rb'))


@bot.message_handler(commands=['expenses'])
def show_current_expenses(message):
    '''show the exact number of current expenses'''
    pass
    



try:
    bot.polling()
except RuntimeError:
    os.execv(sys.executable, ['python'] + [sys.argv[0]])    # restart script


with open('expenses.pickle', 'wb') as file:
    pickle.dump(expenses, file)


##################################ideas
# overview all expenses
# track dates of expenses (discover behavior)

##################################to do
# add commands to bot father
# set up code on raspPI
# replace print statements with logging