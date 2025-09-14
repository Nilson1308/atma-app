import json
import os # Importa o módulo 'os' para aceder às variáveis de ambiente
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.agenda.models import Agendamento
from twilio.rest import Client # Importa o cliente da biblioteca da Twilio

class Command(BaseCommand):
    help = 'Verifica agendamentos próximos e envia lembretes reais via WhatsApp.'

    def handle(self, *args, **options):
        # --- CARREGA AS CREDENCIAIS DE FORMA SEGURA ---
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        twilio_number = os.environ.get('TWILIO_WHATSAPP_NUMBER')

        if not all([account_sid, auth_token, twilio_number]):
            self.stdout.write(self.style.ERROR('As credenciais da Twilio não estão configuradas no ficheiro .env'))
            return

        # Inicializa o cliente da Twilio
        client = Client(account_sid, auth_token)
        # ----------------------------------------------

        agora = timezone.now()
        limite_inferior = agora + timedelta(hours=24)
        limite_superior = agora + timedelta(hours=25)

        agendamentos_para_lembrar = Agendamento.objects.filter(
            data_hora_inicio__gte=limite_inferior,
            data_hora_inicio__lt=limite_superior,
            lembrete_enviado=False,
            status='Agendado',
            paciente__contato_telefone__isnull=False
        ).exclude(paciente__contato_telefone__exact='')

        if not agendamentos_para_lembrar.exists():
            self.stdout.write(self.style.SUCCESS('Nenhum lembrete para enviar no momento.'))
            return

        self.stdout.write(f'Encontrados {agendamentos_para_lembrar.count()} agendamento(s) para enviar lembrete.')
        
        sucessos = 0
        for agendamento in agendamentos_para_lembrar:
            paciente = agendamento.paciente
            
            data_hora_local = timezone.localtime(agendamento.data_hora_inicio)
            data_hora_formatada = data_hora_local.strftime('%d/%m/%Y às %H:%M')
            
            mensagem = f"""
Olá, *{paciente.nome_completo}*! 👋

Lembrete da sua consulta:
*Serviço:* {agendamento.titulo}
*Data e Hora:* {data_hora_formatada}

Por favor, responda com uma das opções:
➡️ *"SIM"* para confirmar.
➡️ *"NÃO"* para cancelar.
➡️ *"REAGENDAR"* para solicitar um novo horário.

Até breve!
"""
            
            # Limpa o número de telefone do paciente para o formato internacional
            numero_paciente_limpo = ''.join(filter(str.isdigit, paciente.contato_telefone))
            if len(numero_paciente_limpo) == 11:
                 numero_paciente_formatado = f'whatsapp:+55{numero_paciente_limpo}'
            else: # Assume outros formatos se necessário
                 numero_paciente_formatado = f'whatsapp:+{numero_paciente_limpo}'

            try:
                # --- FAZ A CHAMADA REAL À API DA TWILIO ---
                message = client.messages.create(
                              # CORREÇÃO APLICADA AQUI
                              from_=f'whatsapp:{twilio_number}',
                              body=mensagem.strip(),
                              to=numero_paciente_formatado
                          )
                # -------------------------------------------

                self.stdout.write(self.style.SUCCESS(f'Mensagem enviada para {paciente.contato_telefone} (SID: {message.sid})'))
                agendamento.lembrete_enviado = True
                agendamento.save()
                sucessos += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Falha ao enviar mensagem para {paciente.contato_telefone}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Processo finalizado. {sucessos} lembrete(s) enviado(s) com sucesso.'))

