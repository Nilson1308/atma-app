import json
from django.core.management.base import BaseCommand
from django.utils import timezone # Importação do timezone do Django
from datetime import timedelta
from apps.agenda.models import Agendamento

class Command(BaseCommand):
    help = 'Verifica agendamentos próximos e simula o envio de lembretes via WhatsApp.'

    def handle(self, *args, **options):
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
            profissional = agendamento.profissional
            paciente = agendamento.paciente
            
            data_hora_local = timezone.localtime(agendamento.data_hora_inicio)
            data_hora_formatada = data_hora_local.strftime('%d/%m/%Y às %H:%M')
            
            link_confirmacao = f"http://localhost:8000/api/agendamentos/confirmar/{agendamento.token_confirmacao}/"

            # --- MENSAGEM ATUALIZADA ---
            mensagem = f"""
Olá, *{paciente.nome_completo}*! 👋

Este é um lembrete da sua consulta agendada:
*Serviço:* {agendamento.titulo}
*Profissional:* {profissional.nome_completo}
*Data e Hora:* {data_hora_formatada}

Para confirmar sua presença, clique no link abaixo ou simplesmente responda *"SIM"* a esta mensagem.
{link_confirmacao}

Até breve!
"""
            
            payload_simulado = {
                'from': 'whatsapp:+14155238886',
                'to': f'whatsapp:{paciente.contato_telefone}',
                'body': mensagem.strip()
            }

            self.stdout.write("-" * 60)
            self.stdout.write(self.style.SUCCESS(f'SIMULANDO ENVIO para {paciente.contato_telefone}:'))
            self.stdout.write(json.dumps(payload_simulado, indent=2, ensure_ascii=False))
            self.stdout.write("-" * 60)

            agendamento.lembrete_enviado = True
            agendamento.save()
            sucessos += 1

        self.stdout.write(self.style.SUCCESS(f'Processo finalizado. {sucessos} lembrete(s) simulado(s) com sucesso.'))