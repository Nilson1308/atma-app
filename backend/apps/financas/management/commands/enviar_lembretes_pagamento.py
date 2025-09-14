import json
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.financas.models import Transacao

class Command(BaseCommand):
    help = 'Verifica transações pendentes e envia lembretes de pagamento.'

    def handle(self, *args, **options):
        hoje = timezone.localdate()
        # Define o critério: transações criadas há 3 dias ou mais
        data_limite = hoje - timedelta(days=3)

        transacoes_pendentes = Transacao.objects.filter(
            status='pendente',
            data_transacao__lte=data_limite,
            lembrete_pagamento_enviado=False,
            paciente__contato_telefone__isnull=False
        ).exclude(paciente__contato_telefone__exact='')

        if not transacoes_pendentes.exists():
            self.stdout.write(self.style.SUCCESS('Nenhum lembrete de pagamento para enviar.'))
            return

        self.stdout.write(f'Encontrados {transacoes_pendentes.count()} pagamento(s) pendente(s) para enviar lembrete.')
        
        sucessos = 0
        for transacao in transacoes_pendentes:
            paciente = transacao.paciente
            profissional = transacao.profissional
            
            data_formatada = transacao.data_transacao.strftime('%d/%m/%Y')
            valor_formatado = f"R$ {transacao.valor_cobrado:.2f}".replace('.', ',')

            mensagem = f"""
Olá, *{paciente.nome_completo}*!

Notei que o pagamento referente ao serviço de *{transacao.servico_prestado.nome_servico}* (realizado em {data_formatada}), no valor de *{valor_formatado}*, ainda está pendente.

Poderia, por favor, verificar? Se já tiver efetuado o pagamento, por favor, desconsidere esta mensagem.

Qualquer dúvida, estou à disposição!

Atenciosamente,
*{profissional.nome_completo}*
"""
            
            payload_simulado = {
                'from': 'whatsapp:+14155238886',
                'to': f'whatsapp:{paciente.contato_telefone}',
                'body': mensagem.strip()
            }

            self.stdout.write("-" * 60)
            self.stdout.write(self.style.SUCCESS(f'SIMULANDO ENVIO DE LEMBRETE DE PAGAMENTO para {paciente.contato_telefone}:'))
            self.stdout.write(json.dumps(payload_simulado, indent=2, ensure_ascii=False))
            self.stdout.write("-" * 60)

            transacao.lembrete_pagamento_enviado = True
            transacao.save()
            sucessos += 1

        self.stdout.write(self.style.SUCCESS(f'Processo finalizado. {sucessos} lembrete(s) de pagamento simulado(s) com sucesso.'))
