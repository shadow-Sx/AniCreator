import threading
import time
import bot1
import bot2
import bot3

def run_bot1():
    print("Bot1 ishga tushdi...")
    bot1.bot.polling(non_stop=True)

def run_bot2():
    print("Bot2 ishga tushdi...")
    bot2.bot.polling(non_stop=True)

def run_bot3():
    print("Bot3 ishga tushdi...")
    bot3.bot.polling(non_stop=True)

if __name__ == "__main__":
    # Har bir botni alohida thread'da ishga tushiramiz
    t1 = threading.Thread(target=run_bot1, name="Bot1")
    t2 = threading.Thread(target=run_bot2, name="Bot2")
    t3 = threading.Thread(target=run_bot3, name="Bot3")

    t1.start()
    t2.start()
    t3.start()

    # Asosiy thread'ni ochiq ushlab turish uchun
    while True:
        time.sleep(1)
