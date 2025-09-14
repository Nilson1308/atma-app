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
        print("\n" + "="*20 + " WEBHOOK INICIADO " + "="*20)
        try:
            remetente = request.data.get('From', '')
            corpo_mensagem = request.data.get('Body', '')
            print(f"Recebido de: {remetente}, Mensagem: '{corpo_mensagem}'")

            numero_paciente_webhook = ''.join(filter(str.isdigit, remetente))[-11:]
            if not numero_paciente_webhook or not corpo_mensagem:
                return Response({"status": "erro"}, status=400)

            print("Passo 1: A procurar o paciente...")
            paciente = next((p for p in Paciente.objects.filter(contato_telefone__isnull=False) if ''.join(filter(str.isdigit, p.contato_telefone)).endswith(numero_paciente_webhook)), None)
            if not paciente:
                raise Paciente.DoesNotExist

            print(f"Passo 2: Paciente encontrado: {paciente.nome_completo}")

            # ... (Lógica de respostas rápidas: SIM, NÃO, etc. - sem alterações)

            # --- LÓGICA DA IA MOVIDA DIRETAMENTE PARA AQUI ---
            print("Passo 4: Nenhuma resposta rápida. A chamar a IA diretamente na View...")
            GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
            if not GEMINI_API_KEY:
                print("!!! ERRO CRÍTICO: GEMINI_API_KEY não encontrada no ficheiro .env !!!")
                return Response({"status": "erro_configuracao"})
            
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash-latest')

            prompt = f"""
            Você é uma secretária virtual para {paciente.cadastrado_por.nome_completo}, um(a) profissional de saúde.
            Um paciente enviou a seguinte mensagem via WhatsApp: "{corpo_mensagem}"

            A sua tarefa é analisar esta mensagem e determinar a intenção do paciente.
            Responda com APENAS uma das seguintes palavras-chave:
            - AGENDAR
            - DUVIDA
            - DESCONHECIDO
            """
            
            try:
                response = model.generate_content(prompt)
                intent = response.text.strip().upper()
            except Exception as e:
                print(f"!!! ERRO DIRETO DA GEMINI API: {e}")
                intent = "ERRO_API"
            # --------------------------------------------------

            print(f"Passo 5: Intenção da IA detetada: {intent}")

            if intent == "AGENDAR":
                print("Passo 6: A gerar resposta com horários...")
                # Continuamos a usar o manager para as outras lógicas que já funcionam
                ai_manager = GeminiAIManager(profissional=paciente.cadastrado_por)
                resposta_ia = ai_manager.gerar_resposta_com_horarios()
                
                print("Passo 7: A enviar resposta para o paciente...")
                envio_sucesso = responder_paciente_via_whatsapp(paciente.contato_telefone, resposta_ia)
                print(f"Passo 8: Estado do envio: {'SUCESSO' if envio_sucesso else 'FALHA'}")
                return Response({"status": "processado"})

            else:
                print("--> Ação: Intenção não é 'AGENDAR'. A terminar o processo.")
                return Response({"status": "info"})

        except Paciente.DoesNotExist:
            return Response({"status": "erro", "mensagem": "Paciente não encontrado."}, status=404)
        except Exception as e:
            traceback.print_exc()
            return Response({"status": "erro", "mensagem": "Erro interno do servidor."}, status=500)