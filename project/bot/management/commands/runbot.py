import asyncio

from django.core.management.base import BaseCommand

from ...mybot import bot


class Command(BaseCommand):
    help = 'help'

    def handle(self, *args, **options):
        asyncio.run(bot.polling())
