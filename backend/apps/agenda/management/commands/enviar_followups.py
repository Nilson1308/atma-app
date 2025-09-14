import json
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.agenda.models import Agendamento

class Command(BaseCommand):
    help = 'Verifica agendamentos realizados no dia anterior e envia uma mensagem de follow-up.'

    def handle(self, *args, **options):
        # Define a data alvo como "ontem"
        data_alvo = timezone.localdate() - timedelta(days=1)

        # Encontra agendamentos realizados ontem que ainda não receberam follow-up
        agendamentos_para_followup = Agendamento.objects.filter(
            status='Realizado',
            data_hora_inicio__date=data_alvo,
            follow_up_enviado=False,
            paciente__contato_telefone__isnull=False
        ).exclude(paciente__contato_telefone__exact='')

        if not agendamentos_para_followup.exists():
            self.stdout.write(self.style.SUCCESS('Nenhum follow-up para enviar hoje.'))
            return

        self.stdout.write(f'Encontrados {agendamentos_para_followup.count()} agendamento(s) para enviar follow-up.')
        
        sucessos = 0
        for agendamento in agendamentos_para_followup:
            paciente = agendamento.paciente
            profissional = agendamento.profissional
            
            mensagem = f"""
Olá, *{paciente.nome_completo}*!

Passando para saber como se sente após a nossa consulta de ontem. 
Espero que esteja tudo bem!

Se tiver alguma dúvida ou se algo novo surgir, não hesite em contactar.

Com os melhores cumprimentos,
*{profissional.nome_completo}*
"""
            
            payload_simulado = {
                'from': 'whatsapp:+14155238886',
                'to': f'whatsapp:{paciente.contato_telefone}',
                'body': mensagem.strip()
            }

            self.stdout.write("-" * 60)
            self.stdout.write(self.style.SUCCESS(f'SIMULANDO ENVIO DE FOLLOW-UP para {paciente.contato_telefone}:'))
            self.stdout.write(json.dumps(payload_simulado, indent=2, ensure_ascii=False))
            self.stdout.write("-" * 60)

            # Marca o follow-up como enviado para não enviar novamente
            agendamento.follow_up_enviado = True
            agendamento.save()
            sucessos += 1

        self.stdout.write(self.style.SUCCESS(f'Processo finalizado. {sucessos} follow-up(s) simulado(s) com sucesso.'))

    
