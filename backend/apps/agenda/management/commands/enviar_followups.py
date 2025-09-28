import json
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.agenda.models import Agendamento
from apps.agenda.views import responder_paciente_via_whatsapp # Reutiliza nossa função de envio

class Command(BaseCommand):
    help = 'Verifica agendamentos realizados no dia anterior e envia uma mensagem de follow-up com NPS.'

    def handle(self, *args, **options):
        data_alvo = timezone.localdate() - timedelta(days=1)

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
            
            mensagem = f"""
Olá, *{paciente.nome_completo.split(' ')[0]}*!

Espero que esteja tudo bem após nossa consulta de ontem.

Para sempre melhorarmos nosso atendimento, você poderia nos dar uma nota? De 0 a 10, o quanto você nos recomendaria a um amigo ou familiar?

Sua opinião é muito importante para nós!
"""
            
            # Usamos a função de envio real/simulada que já criamos
            enviado = responder_paciente_via_whatsapp(paciente.contato_telefone, mensagem.strip())

            if enviado:
                self.stdout.write(self.style.SUCCESS(f'Follow-up com NPS enviado para {paciente.nome_completo}'))
                # --- ATUALIZAÇÃO IMPORTANTE ---
                # Marcamos o paciente com um estado para que a IA saiba que a próxima resposta é a nota
                paciente.conversation_state = f'AWAITING_NPS_{agendamento.id}'
                paciente.save()

                agendamento.follow_up_enviado = True
                agendamento.save()
                sucessos += 1
            else:
                 self.stdout.write(self.style.ERROR(f'Falha ao enviar follow-up para {paciente.nome_completo}'))


        self.stdout.write(self.style.SUCCESS(f'Processo finalizado. {sucessos} follow-up(s) enviado(s) com sucesso.'))