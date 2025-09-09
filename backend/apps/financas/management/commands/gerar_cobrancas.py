from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.users.models import Paciente
from apps.agenda.models import Agendamento
from apps.financas.models import Transacao

class Command(BaseCommand):
    help = 'Gera transações pendentes para pacientes com dia de cobrança definido.'

    def handle(self, *args, **options):
        hoje = timezone.localdate()
        dia_atual = hoje.day

        # 1. Encontra todos os pacientes que têm o dia de cobrança igual ao dia de hoje.
        pacientes_para_cobrar = Paciente.objects.filter(dia_cobranca=dia_atual)

        if not pacientes_para_cobrar.exists():
            self.stdout.write(self.style.SUCCESS('Nenhum paciente para cobrar hoje.'))
            return

        self.stdout.write(f'Encontrados {pacientes_para_cobrar.count()} paciente(s) com dia de cobrança hoje ({dia_atual}).')

        contador_transacoes = 0
        for paciente in pacientes_para_cobrar:
            # 2. Para cada paciente, busca agendamentos realizados que ainda não têm transação.
            agendamentos_a_faturar = Agendamento.objects.filter(
                paciente=paciente,
                status='Realizado',
                transacao__isnull=True, # Garante que ainda não foi faturado
                servico__isnull=False  # Garante que há um serviço a ser cobrado
            )

            if not agendamentos_a_faturar.exists():
                continue

            self.stdout.write(f'  - Gerando cobranças para o paciente: {paciente.nome_completo}')

            # 3. Cria uma transação para cada agendamento pendente.
            for agendamento in agendamentos_a_faturar:
                Transacao.objects.create(
                    profissional=agendamento.profissional,
                    paciente=agendamento.paciente,
                    agendamento=agendamento,
                    servico_prestado=agendamento.servico,
                    valor_cobrado=agendamento.servico.valor_padrao,
                    status='pendente',
                    # A data da transação é o dia de hoje (dia da cobrança)
                    data_transacao=hoje 
                )
                contador_transacoes += 1
                self.stdout.write(f'    - Transação criada para o agendamento de {agendamento.data_hora_inicio.strftime("%d/%m/%Y")}')

        self.stdout.write(self.style.SUCCESS(f'Processo finalizado. {contador_transacoes} nova(s) transação(ões) criada(s).'))