import os
from django.core.management.base import BaseCommand
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

class Command(BaseCommand):
    help = 'Envia uma mensagem de teste direta via Twilio para diagnosticar problemas.'

    def add_arguments(self, parser):
        parser.add_argument('phone_number', type=str, help='O número de telefone de destino no formato 55119XXXXXXXX.')

    def handle(self, *args, **options):
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        twilio_number = os.environ.get('TWILIO_WHATSAPP_NUMBER')
        destination_number = options['phone_number']

        if not all([account_sid, auth_token, twilio_number]):
            self.stdout.write(self.style.ERROR('As credenciais da Twilio não estão configuradas no .env'))
            return

        client = Client(account_sid, auth_token)
        formatted_destination = f'whatsapp:+{destination_number}'
        formatted_from = f'whatsapp:{twilio_number}'
        
        test_message = "Olá! Esta é uma mensagem de teste direto do Atma App. Se você recebeu isso, a comunicação com a Twilio está funcionando."

        self.stdout.write(self.style.WARNING(f"Tentando enviar mensagem de '{formatted_from}' para '{formatted_destination}'..."))

        try:
            message = client.messages.create(
                              from_=formatted_from,
                              body=test_message,
                              to=formatted_destination
                          )
            self.stdout.write(self.style.SUCCESS(f'Mensagem enviada com sucesso! SID: {message.sid}'))
            self.stdout.write(self.style.SUCCESS('Verifique seu WhatsApp.'))

        except TwilioRestException as e:
            self.stdout.write(self.style.ERROR(f'Falha ao enviar mensagem via Twilio: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ocorreu um erro inesperado: {e}'))