# ExpenseTrackerBot
Telegram Bot to track expenses and plot them. 

## Create a Bot 
The script handles everything to track expenses with a Telegram Bot, but of course you'll have to create such a bot first. Be aware that all Telegram Bots are public, so anyone who stumbles across your bot is able to use it. (You could add usage restrictions by white lising user IDs. You can find your ID by asking another bot @userinfobot.)

### Set up
Create a bot with @BotFather on Telegram. You'll receive an api token which you have to save to a file called 'api_token.txt' in this same directory. 

For more convenient use, send the commands to @BotFather (copy-paste the text from 'commands.txt') by typing /setcommands. You can also add a description for your Bot with /setdescription.

You're all set up!

### Prerequisites

Install these python libraries:
```
$ pip install pyTelegramBotAPI
$ pip install seaborn

```

## Features
You can now start using your bot!

Every time you reset the expenses, they get saved to a pickle file including the current date. This allows you to compare expenses (for example every month). 