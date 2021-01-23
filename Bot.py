#!/usr/bin/env python3
'''
todo
    - update list of commands in /help
    - add category: Sparen


info
- the added expenses get saved twice: with and without date (expenses and date_expenses)
    -> let's you analyse spending patterns (i.e. times of the months, week days, etc.)

- when the bot is reset, all previous expenses get saved to a file including the date
    -> kind of back-up for accidental resets
    -> makes long-term analyses possible

- plots do not get saved but are overwritten by the newest plot
    -> if you want to save plots, download the image from the telegram chat

'''
import telebot
from telebot import types
import pickle, re
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import date, datetime
import logging
import os, sys
from InitializeData import initialize

try:
    with open('data/api_token.txt', 'r') as  file:
        token = file.read().strip()
except FileNotFoundError:
    raise Exception("Please create the file 'api_token.txt' that contains your bot's api token.")
    
bot = telebot.TeleBot(token, parse_mode=None)

logging.basicConfig(level=logging.INFO, filename=f"logfiles/logging{date.today()}.log")

current_cat = None


def load_data(file):
    '''load data from file if exists'''
    with open(file, 'rb') as f:
        return pickle.load(f)


def save_data(data, file):
    '''save data to pickle file'''
    with open(file, 'wb') as f:
        pickle.dump(data, f)


def load_keyboard():
    '''load buttons of inline keyboard'''
    with open('data/inline_keyboard.pickle', 'rb') as file:
        return pickle.load(file)


def update_serialized_data():
    '''save updated data to pickle files'''
    save_data(expenses, 'serialized_data/expenses.pickle')
    save_data(date_expense, 'serialized_data/date_of_expenses.pickle')

    
@bot.message_handler(commands=['help'])
def welcome_message(message):
    bot.reply_to(message, '''Welcome to CurBot. I respond to these commands:
    /start - start using the bot
    /help - obtain a list of commands
    /info - learn more about CurBot
    /ausgaben - list and plot all expenses
    /show_fixkosten - show all regular expenses
    /del - delete last expense
    /reset - reset all expenses
    ''')


@bot.message_handler(commands=['info'])
def introduce_bot(message):
    bot.reply_to(message, 'Du kannst ganz einfach neue Ausgaben hinzufügen, indem du /add sendest.' \
        ' Den Betrag schickst du entweder direkt mit dem Befehl, oder danach.\n' \
        'Mit /plot erhältst du eine graphische Übersicht aller Ausgaben, mit /ausgaben die genauen Beträge.\n'\
        'Außerdem kannst du alle Ausgaben zurücksezten (z.B. am Monatsende), sende einfach /reset und bestätige.'
    )


@bot.message_handler(commands=['start'])
def welcome_message(message):
    '''send a welcome message and usage tips'''
    bot.reply_to(message, 'Willkommen! Ich bin ExpenseTrackerBot und fasse deine Ausgaben zusammen.'\
        ' Sende /help für eine Liste meiner Befehle oder füge eine neue Ausgabe hinzu mit /add.'\
            ' Mit /info erhältst du zusätzliche Tips und Tricks.')
    


@bot.message_handler(commands=['add'])
def use_bot(message):
    '''
    use inline keyboard to add expenses or reset them;
    when a new category is added, it needs to be added to be accessed in the bot chat
    '''
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    # include all categories
    inline_keyboards = load_keyboard()
    for kb in inline_keyboards:
        keyboard.add(kb)
    bot.reply_to(message, "Welche Art von Ausgabe möchtest du hinzufügen?", reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda m: True)
    def parse_callback(call):
        ''''''
        global expenses
        cat = call.data

        if cat in categories:
            global current_cat
            current_cat = cat
            bot.reply_to(call.message, 'Bitte nenne den Betrag.')

        else:
            bot.reply_to(call.message, 'Bitte nutze das Inline-Keyboard oder einen Befehl.')



def reset_bot():
    '''
    makes a back-up of current expenses and then resets them
    '''
    no_answer = True
    while no_answer:
        @bot.message_handler(content_types=['text'])
        def double_check(message):
            nonlocal no_answer
            global date_expense, expenses
            if message.text.lower() in ('yes', 'ja'):
                # save current expenses to file
                with open(f'previous_expenses/expenses_{date.today()}.pickle', 'wb') as file:
                    pickle.dump(expenses, file)
                with open(f'previous_expenses/date_expenses_{date.today()}.pickle', 'wb') as file:
                    pickle.dump(date_expense, file)
                # reset expenses
                expenses, date_expense = dict(), dict()
                for cat in categories:
                    expenses[cat] = []
                    date_expense[cat] = []
                update_serialized_data()
                bot.reply_to(message, 'Ausgaben wurden zurückgesetzt.')
                no_answer = False
                logging.info(f'Expenses reset on {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}.')
                logging.basicConfig(filename=f"logfiles/logging{date.today()}.log")
            elif message.text.lower() in ('no', 'nein'):
                bot.reply_to(call.message, 'Abgebrochen. Ausgaben bleiben unverändert.')
                no_answer = False


@bot.message_handler(commands=['reset'])
def reset_expenses(message):
    '''reset expenses (alternative to inline keyboard)'''
    bot.reply_to(message, 'Willst du wirklich alle bisherigen Ausgaben löschen?')
    reset_bot()


@bot.message_handler(regexp='[0-9]+([.,][0-9]+)?')
def get_expense(message):
    '''any number types into the chat will be considered as expense
    as long as there is a current_cat(egory)'''
    global current_cat
    # numbers are only considered when there is an active category (avoids spam)
    if current_cat:
        try:
            exp = float(message.text)
        except ValueError:
            # substitute , with .
            exp = float(message.text.replace(',', '.'))

        expenses[current_cat].append(exp)
        date_expense[current_cat].append((exp, datetime.today()))
        # save updated data to pickle files
        update_serialized_data()
        bot.reply_to(message, f'{exp}€ wurden zu {current_cat} hinzugefügt.')
        print(expenses)
        logging.info(f'New expense was added on {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}.')
        current_cat = None
    else:
        bot.reply_to(message, 'Gib eine Kategorie an mit /start oder /add.')


@bot.message_handler(commands=['del'])
def del_expense(message):
    '''Deletes most recently added expense for 
    a requested category'''
    bot.reply_to(message, 'Von welcher Kategorie willst du die letzte Ausgabe löschen?')

    @bot.message_handler(content_types=['text'], func=lambda m: m.text in categories)
    def del_category_expense(message):
        global expenses
        cat = message.text
        try:
            del expenses[cat][-1]
            del date_expense[cat][-1]
            update_serialized_data()
            bot.reply_to(message, f'Die letzte Ausgabe für {cat} wurde gelöscht.')
            logging.info(f'Expense deleted added on {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}.')
        except IndexError:
            bot.reply_to(message, f'Keine Ausgaben für {cat}.')



@bot.message_handler(commands=['ausgaben'])
def plot_expenses(message):
    exps, cats = list(), list()
    overview_text = '' 
    total_sum = 0

    for cat in categories:
        overview_text += f'{cat}: {sum(expenses[cat])}€\n'
        total_sum += sum(expenses[cat])
        if expenses[cat]:
            exps.append(sum(expenses[cat]))
            cats.append(cat)

    if total_sum != 0:
        bot.reply_to(message, f'Gesamte Ausgaben bisher: {total_sum}€')
        bot.reply_to(message, overview_text)

        # set style for bar chart
        sns.set_style('darkgrid')
        sns.set_palette('crest')

        sns.barplot(cats, exps)
        plt.ylabel('Ausgaben in €')

        # save plot to file and send to chat
        plt.savefig('ausgaben.png')
        bot.send_photo(message.chat.id, photo=open('ausgaben.png', 'rb'))

    else:
        bot.reply_to(message, 'Keine Ausgaben bisher.' )
    


@bot.message_handler(commands=['show_fixkosten'])
def monthly_expenses(message):
    '''calculate and update fix monthly expenses'''
    try:
        with open('serialized_data/regular_expenses.pickle', 'rb') as f:
            fix_expenses = pickle.load(f)
    except FileNotFoundError:
        # insert values for each category
        fix_expenses = {'Miete': 0, 'Strom': 0, 'Gebühren': 0, 'Internet': 0, 'Fitness': 0 ,'TV': 0}
        save_data(fix_expenses, 'serialized_data/regular_expenses.pickle')

    overview = f'Deine monatlichen Fixkosten liegen bei {sum(fix_expenses.values())}:\n'

    # plot data
    exps, cats = list(), list()
    for cat, val in fix_expenses.items():
        exps.append(val)
        cats.append(cat)
        overview += f'{cat}: {val}\n'

    bot.reply_to(message, overview)

    # set style for bar chart
    sns.set_style('darkgrid')
    sns.set_palette('crest')

    sns.barplot(cats, exps)
    plt.ylabel('Kosten in €')

    # save plot to file and send to chat
    plt.savefig('fixkosten.png')
    bot.send_photo(message.chat.id, photo=open('fixkosten.png', 'rb'))


# load data
categories = load_data('data/categories.pickle')
expenses = load_data('serialized_data/expenses.pickle')
date_expense = load_data('serialized_data/date_of_expenses.pickle')


try:
    bot.polling()
except RuntimeError:
    os.execv(sys.executable, ['python'] + [sys.argv[0]])    # restart script

