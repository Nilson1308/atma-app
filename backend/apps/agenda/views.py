import os
import traceback
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import google.generativeai as genai

from apps.users.models import Paciente
from .ia_manager import GeminiAIManager
from .models import Agendamento
from .serializers import AgendamentoSerializer

def responder_paciente_via_whatsapp(numero_destinatario, mensagem):
    """
    Função auxiliar para enviar respostas via Twilio WhatsApp API.
    """
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    twilio_number = os.environ.get('TWILIO_WHATSAPP_NUMBER')

    if not all([account_sid, auth_token, twilio_number]):
        print("!!! ERRO CRÍTICO: Credenciais da Twilio não configuradas no .env !!!")
        return False

    try:
        client = Client(account_sid, auth_token)
        numero_limpo = ''.join(filter(str.isdigit, numero_destinatario))
        
        if len(numero_limpo) == 11:
            numero_formatado = f'whatsapp:+55{numero_limpo}'
        else:
            numero_formatado = f'whatsapp:+{numero_limpo}'

        message = client.messages.create(
            from_=f'whatsapp:{twilio_number}',
            body=mensagem,
            to=numero_formatado
        )
        print(f"--> Mensagem enviada com sucesso para {numero_destinatario} (SID: {message.sid})")
        return True
    except TwilioRestException as e:
        print(f"!!! ERRO AO ENVIAR WHATSAPP via Twilio: {e}")
        return False
    except Exception as e:
        print(f"!!! ERRO INESPERADO ao enviar WhatsApp: {e}")
        return False

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
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):

        profissional = paciente.cadastrado_por
        try:
            assinatura = profissional.assinatura
            if not assinatura.ativa or assinatura.plano.nome == 'BASICO':
                print(f"--> Ação Bloqueada: Profissional {profissional.email} está no plano BÁSICO ou sem assinatura ativa.")
                # Não faz nada. A mensagem do paciente será ignorada pela IA.
                return Response({"status": "plano_incompativel"})
        except Assinatura.DoesNotExist:
            print(f"--> Ação Bloqueada: Profissional {profissional.email} não possui assinatura.")
            return Response({"status": "sem_assinatura"})
            
        print("\n" + "="*20 + " WEBHOOK INICIADO " + "="*20)
        try:
            remetente = request.data.get('From', '')
            corpo_mensagem_original = request.data.get('Body', '').strip()
            corpo_mensagem_upper = corpo_mensagem_original.upper()
            print(f"Recebido de: {remetente}, Mensagem: '{corpo_mensagem_original}'")

            numero_paciente_webhook = ''.join(filter(str.isdigit, remetente))[-11:]
            if not numero_paciente_webhook or not corpo_mensagem_original:
                return Response({"status": "erro"}, status=400)

            paciente = next((p for p in Paciente.objects.filter(contato_telefone__isnull=False) if ''.join(filter(str.isdigit, p.contato_telefone)).endswith(numero_paciente_webhook)), None)
            if not paciente:
                raise Paciente.DoesNotExist
            
            print(f"Passo 2: Paciente encontrado: {paciente.nome_completo}")
            ai_manager = GeminiAIManager(profissional=paciente.cadastrado_por)

            # --- FLUXO 1: RESPOSTA A UM LEMBRETE DE CONFIRMAÇÃO ---
            agendamento_pendente = Agendamento.objects.filter(paciente=paciente, status__in=['Agendado'], data_hora_inicio__gte=timezone.now()).order_by('data_hora_inicio').first()
            if agendamento_pendente:
                if corpo_mensagem_upper == 'SIM':
                    print("--> Ação: Confirmação de agendamento.")
                    agendamento_pendente.status = 'Confirmado'
                    agendamento_pendente.save()
                    responder_paciente_via_whatsapp(paciente.contato_telefone, "Obrigado por confirmar! Sua consulta está garantida.")
                    return Response({"status": "confirmado"}) # <-- Finaliza aqui

                if corpo_mensagem_upper == 'NÃO' or corpo_mensagem_upper == 'REAGENDAR':
                    print("--> Ação: Cancelamento e início de reagendamento.")
                    agendamento_pendente.status = 'Cancelado'
                    agendamento_pendente.save()
                    # A mensagem será tratada como um novo pedido de agendamento pelo fluxo abaixo
            
            # --- FLUXO 2: CONVERSA DE AGENDAMENTO (NOVO OU CONTINUAÇÃO) ---
            analise = ai_manager.analisar_mensagem_paciente(corpo_mensagem_original)
            intent = analise.get('intent')
            print(f"--> Análise da IA: {analise}")

            if intent == "AGENDAR" or (agendamento_pendente and (corpo_mensagem_upper == 'NÃO' or corpo_mensagem_upper == 'REAGENDAR')):
                print("--> Ação: Iniciar agendamento. Perguntando preferências...")
                resposta_ia = ai_manager.gerar_pergunta_preferencia(paciente.nome_completo)
                responder_paciente_via_whatsapp(paciente.contato_telefone, resposta_ia)
                return Response({"status": "aguardando_preferencia"})

            elif intent == "AGENDAR_COM_PREFERENCIA":
                print("--> Ação: Paciente informou uma preferência.")
                preferencias = ai_manager.extrair_preferencias(corpo_mensagem_original)
                print(f"--> Preferências extraídas: {preferencias}")
                
                horarios = ai_manager.encontrar_horarios_disponiveis(preferencias)
                resposta_ia = ai_manager.gerar_resposta_com_horarios(paciente.nome_completo, horarios)
                responder_paciente_via_whatsapp(paciente.contato_telefone, resposta_ia)
                return Response({"status": "horarios_enviados"})

            elif intent == "ESCOLHEU_HORARIO":
                print("--> Ação: Paciente escolheu um horário (implementação futura).")
                resposta_ia = "Perfeito! Só um momento enquanto eu confirmo e finalizo o seu agendamento."
                responder_paciente_via_whatsapp(paciente.contato_telefone, resposta_ia)
                return Response({"status": "confirmacao_pendente"})

            else: # DUVIDA ou DESCONHECIDO
                print("--> Ação: Intenção não é de agendamento.")
                return Response({"status": "info"})

        except Paciente.DoesNotExist:
            return Response({"status": "erro", "mensagem": "Paciente não encontrado."}, status=404)
        except Exception as e:
            traceback.print_exc()
            return Response({"status": "erro", "mensagem": "Erro interno do servidor."}, status=500)

from .models import HorarioTrabalho, ExcecaoHorario
from .serializers import HorarioTrabalhoSerializer, ExcecaoHorarioSerializer

class HorarioTrabalhoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para o profissional gerenciar seus horários de trabalho padrão.
    """
    serializer_class = HorarioTrabalhoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """ Retorna apenas os horários que pertencem ao profissional logado. """
        return HorarioTrabalho.objects.filter(profissional=self.request.user)

    def perform_create(self, serializer):
        """ Associa o profissional logado ao criar um novo horário. """
        serializer.save(profissional=self.request.user)

class ExcecaoHorarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para o profissional gerenciar suas exceções de horário (folgas, feriados, etc.).
    """
    serializer_class = ExcecaoHorarioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """ Retorna apenas as exceções que pertencem ao profissional logado. """
        # Filtra por datas a partir de hoje para não carregar o histórico completo desnecessariamente
        return ExcecaoHorario.objects.filter(
            profissional=self.request.user,
            data__gte=timezone.localdate()
        )

    def perform_create(self, serializer):
        """ Associa o profissional logado ao criar uma nova exceção. """
        serializer.save(profissional=self.request.user)