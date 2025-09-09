from rest_framework import viewsets, permissions
from .models import Agendamento
from .serializers import AgendamentoSerializer
from apps.financas.models import Transacao
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from rest_framework.response import Response
from django.utils import timezone
from apps.users.models import Paciente

class AgendamentoViewSet(viewsets.ModelViewSet):
    serializer_class = AgendamentoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Agendamento.objects.filter(profissional=self.request.user)

    def perform_create(self, serializer):
        serializer.save(profissional=self.request.user)

    def perform_update(self, serializer):
        old_status = serializer.instance.status
        
        instance = serializer.save()
        
        new_status = instance.status

        if new_status == 'Realizado' and old_status != 'Realizado':
            if instance.paciente.dia_cobranca is None:
                if instance.servico and not Transacao.objects.filter(agendamento=instance).exists():
                    Transacao.objects.create(
                        profissional=instance.profissional,
                        paciente=instance.paciente,
                        agendamento=instance,
                        servico_prestado=instance.servico,
                        valor_cobrado=instance.servico.valor_padrao,
                        status='pendente'
                    )
        
        return instance


class PacienteAgendamentoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AgendamentoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        paciente_pk = self.kwargs.get('paciente_pk')
        return Agendamento.objects.filter(
            paciente__pk=paciente_pk,
            profissional=self.request.user
        )

class ConfirmarAgendamentoView(APIView):
    """
    View pública para o paciente confirmar o agendamento através de um token.
    """
    permission_classes = [permissions.AllowAny] # Não exige autenticação

    def get(self, request, token, *args, **kwargs):
        agendamento = get_object_or_404(Agendamento, token_confirmacao=token)

        # Altera o status para 'Confirmado'
        agendamento.status = 'Confirmado'
        agendamento.save()
        
        # Retorna uma mensagem simples de sucesso em HTML
        html_response = """
        <html>
            <head>
                <title>Confirmação de Consulta</title>
                <style>
                    body { font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f0f2f5; }
                    .card { background-color: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; }
                    h1 { color: #2ecc71; }
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>✅ Presença Confirmada!</h1>
                    <p>Sua consulta foi confirmada com sucesso.</p>
                    <p>Agradecemos a sua colaboração.</p>
                </div>
            </body>
        </html>
        """
        return HttpResponse(html_response)

class WhatsAppWebhookView(APIView):
    """
    Webhook para receber e processar as respostas dos pacientes via WhatsApp.
    """
    permission_classes = [permissions.AllowAny] # Público para receber chamadas da API do WhatsApp

    def post(self, request, *args, **kwargs):
        # A estrutura dos dados pode variar dependendo do provedor (ex: Twilio)
        # Vamos simular uma estrutura comum: {'from': 'whatsapp:+5511...', 'body': 'Sim'}
        remetente = request.data.get('from', '')
        corpo_mensagem = request.data.get('body', '').strip().upper()

        # Limpa o número de telefone que recebemos para conter apenas os últimos 11 dígitos
        numero_paciente_webhook = ''.join(filter(str.isdigit, remetente))[-11:]

        if not numero_paciente_webhook or not corpo_mensagem:
            return Response({"status": "erro", "mensagem": "Dados inválidos."}, status=400)

        # Palavras-chave para confirmação
        palavras_de_confirmacao = ['SIM', 'CONFIRMO', 'CONFIRMADO', 'OK']

        if corpo_mensagem in palavras_de_confirmacao:
            try:
                # Lógica de busca robusta: Compara apenas os dígitos dos números
                paciente_encontrado = None
                for p in Paciente.objects.filter(contato_telefone__isnull=False):
                    db_telefone_digits = ''.join(filter(str.isdigit, p.contato_telefone))
                    if db_telefone_digits.endswith(numero_paciente_webhook):
                        paciente_encontrado = p
                        break
                
                if not paciente_encontrado:
                    raise Paciente.DoesNotExist

                paciente = paciente_encontrado
                # Encontra o próximo agendamento "Agendado" para este paciente
                agendamento_para_confirmar = Agendamento.objects.filter(
                    paciente=paciente,
                    status='Agendado',
                    data_hora_inicio__gte=timezone.now()
                ).order_by('data_hora_inicio').first()

                if agendamento_para_confirmar:
                    agendamento_para_confirmar.status = 'Confirmado'
                    agendamento_para_confirmar.save()
                    print(f"Agendamento de {paciente.nome_completo} confirmado por resposta de WhatsApp.")
                    return Response({"status": "sucesso", "mensagem": "Agendamento confirmado."})
                else:
                    return Response({"status": "info", "mensagem": "Nenhum agendamento pendente encontrado."})

            except Paciente.DoesNotExist:
                return Response({"status": "erro", "mensagem": "Paciente não encontrado."}, status=404)
            except Exception as e:
                print(f"Erro no webhook do WhatsApp: {e}")
                return Response({"status": "erro", "mensagem": "Erro interno do servidor."}, status=500)

        return Response({"status": "info", "mensagem": "Mensagem não é uma confirmação."})