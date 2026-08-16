import datetime
import psutil


def get_time():
    now = datetime.datetime.now()
    return now.strftime("It is %I:%M %p.")


def get_date():
    today = datetime.datetime.now()
    return today.strftime("Today is %A, %d %B %Y.")


def get_battery():

    battery = psutil.sensors_battery()

    if battery is None:
        return "I couldn't detect a battery on this computer."

    percentage = battery.percent

    if battery.power_plugged:
        return f"Battery is at {percentage:.0f}% and the computer is plugged in."

    return f"Battery is at {percentage:.0f}%."