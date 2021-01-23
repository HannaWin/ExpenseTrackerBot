#!/usr/bin/env python3

'''
initialize required data when using bot for the first time
and
update data when new category gets added
'''
import pickle
from telebot import types


# define your categories!
categories = ['Haushalt', 'Hobby', 'Bildung', 'Kleidung', 'Bücher', 'Wohnung', 'Ausgehen', 'Gebühren', 'Geschenke', 'Transport', 'Lebensmittel']

def initialize():
    '''initializes categories, expenses, date expenses, and keyboard'''
    expenses, date_expenses = {}, {}
    for cat in categories:
        expenses[cat] = []
        date_expenses[cat] = []

    save_data(categories, 'data/categories.pickle')
    save_data(expenses, 'serialized_data/expenses.pickle')
    save_data(date_expenses, 'serialized_data/date_of_expenses.pickle')

    create_inline_keyboard()


def create_inline_keyboard():
    '''initalize inline keyboard'''
    inline_keyboards = list()
    for cat in categories:
        kb = types.InlineKeyboardButton(text=cat, callback_data=cat)
        inline_keyboards.append(kb)

    with open('data/inline_keyboard.pickle', 'wb') as f:
        pickle.dump(inline_keyboards, f)


def save_data(data, file):
    '''save data to pickle file'''
    with open(file, 'wb') as f:
        pickle.dump(data, f)


def load_data(file):
    '''load data from file'''
    with open(file, 'rb') as f:
        return pickle.load(f)


def update(new_cats):
    '''update data with new category|ies'''
    expenses = load_data('serialized_data/expenses.pickle')
    date_expenses = load_data('serialized_data/date_of_expenses.pickle')

    for cat in new_cats:
        categories.append(cat)
        expenses[cat] = 0
        date_expenses[cat] = 0
    
    save_data(categories, 'data/categories.pickle')
    save_data(expenses, 'serialized_data/expenses.pickle')
    save_data(date_expenses, 'serialized_data/date_expenses.pickle')

    create_inline_keyboard()






