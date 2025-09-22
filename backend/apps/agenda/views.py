import os
import traceback
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta 
from django.core.cache import cache
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import google.generativeai as genai

from apps.users.models import Paciente, Conta, Assinatura
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
        """
        Filtra os agendamentos com base no plano e na função do usuário.
        - Plano Premium e função 'Profissional': Vê apenas os seus próprios agendamentos.
        - Outros casos (ex: Proprietário, outros planos): Vê todos os agendamentos da conta.
        """
        user = self.request.user
        assinatura = user.conta.assinatura

        # Verifica se a conta é Premium e se o usuário não é o proprietário
        if assinatura.plano.nome == 'PREMIUM' and user.funcao == 'profissional':
            print(f"--> [Agenda] Usuário {user.email} (Profissional Premium) vendo apenas sua agenda.")
            return Agendamento.objects.filter(profissional=user)
        
        # Para todos os outros casos (Proprietários, planos não-Premium), mostra tudo da conta
        print(f"--> [Agenda] Usuário {user.email} (Admin/Outro Plano) vendo a agenda completa da conta.")
        return Agendamento.objects.filter(profissional__conta=user.conta)

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
            paciente__conta=self.request.user.conta
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
            remetente_full = request.data.get('From', '')
            destinatario_full = request.data.get('To', '')
            corpo_mensagem_original = request.data.get('Body', '').strip()
            
            remetente_num = ''.join(filter(str.isdigit, remetente_full))
            destinatario_num = ''.join(filter(str.isdigit, destinatario_full))

            print(f"Recebido de: {remetente_num}, Para: {destinatario_num}, Mensagem: '{corpo_mensagem_original}'")

            if not remetente_num or not corpo_mensagem_original:
                return Response({"status": "dados_insuficientes"}, status=400)

            conta = Conta.objects.get(whatsapp_number=destinatario_num)
            paciente = Paciente.objects.filter(conta=conta, contato_telefone__contains=remetente_num).first()
            ai_manager = GeminiAIManager(profissional=conta.proprietario)

            # --- FLUXO DE LÓGICA CORRIGIDO ---

            # 1. Checagem de Resposta a Lembrete (Prioridade Máxima)
            corpo_mensagem_upper = corpo_mensagem_original.upper()
            if paciente:
                agendamento_pendente = Agendamento.objects.filter(
                    paciente=paciente, status__in=['Agendado'], 
                    data_hora_inicio__gte=timezone.now()
                ).order_by('data_hora_inicio').first()

                if agendamento_pendente and (corpo_mensagem_upper in ['SIM', 'NÃO', 'REAGENDAR']):
                    if corpo_mensagem_upper == 'SIM':
                        agendamento_pendente.status = 'Confirmado'
                        agendamento_pendente.save()
                        responder_paciente_via_whatsapp(paciente.contato_telefone, "Obrigado por confirmar! Sua consulta está garantida.")
                        return Response({"status": "confirmado"})
                    
                    if corpo_mensagem_upper in ['NÃO', 'REAGENDAR']:
                        agendamento_pendente.status = 'Cancelado'
                        agendamento_pendente.save()
                        # Força o fluxo a entrar na lógica de agendamento, tratando como se o paciente tivesse pedido para agendar
                        return self.handle_paciente_existente(request, paciente, "gostaria de agendar", "AGENDAR", ai_manager)

            # 2. Se não for resposta a lembrete, identifica a intenção geral
            intencao = ai_manager.identificar_intencao_geral(corpo_mensagem_original, conta)
            print(f"--> Intenção da IA Identificada: {intencao}")

            # 3. Direciona para o handler correto com a intenção JÁ IDENTIFICADA
            if paciente:
                return self.handle_paciente_existente(request, paciente, corpo_mensagem_original, intencao, ai_manager)
            else:
                return self.handle_novo_contato(request, conta, remetente_full, corpo_mensagem_original, intencao, ai_manager)

        except Conta.DoesNotExist:
            print(f"--> Erro Crítico: Nenhum profissional/conta associado ao número de destino {destinatario_num}")
            return Response({"status": "conta_nao_encontrada"})
        except Exception as e:
            traceback.print_exc()
            return Response({"status": "erro_geral", "mensagem": str(e)}, status=500)

    def handle_paciente_existente(self, request, paciente, corpo_mensagem_original, intent, ai_manager):
        print(f"--> Ação: Lidando com paciente existente: {paciente.nome_completo} | Intenção: {intent}")
        conta = paciente.conta
        
        try: # Validação de assinatura
            assinatura = conta.assinatura
            if not assinatura.ativa or assinatura.plano.limite_mensagens_ia == 0:
                return Response({"status": "plano_incompativel"})
        except Assinatura.DoesNotExist:
            return Response({"status": "sem_assinatura"})

        cache_key = f"horarios_oferecidos_{paciente.id}"
        horarios_oferecidos_cache = cache.get(cache_key)

        if intent == "ESCOLHEU_HORARIO" and horarios_oferecidos_cache:
            horario_escolhido_utc = ai_manager.extrair_horario_escolhido(corpo_mensagem_original, horarios_oferecidos_cache)
            if horario_escolhido_utc:
                Agendamento.objects.create(paciente=paciente, profissional=conta.proprietario, titulo="Consulta agendada pela IA", data_hora_inicio=horario_escolhido_utc, data_hora_fim=horario_escolhido_utc + timedelta(hours=1), status='Confirmado')
                data_local_formatada = timezone.localtime(horario_escolhido_utc).strftime('%A, %d de %B às %H:%M')
                resposta_ia = f"Perfeito, {paciente.nome_completo.split(' ')[0]}! Seu agendamento para {data_local_formatada} está confirmado. Até lá!"
                responder_paciente_via_whatsapp(paciente.contato_telefone, resposta_ia)
                cache.delete(cache_key)
                return Response({"status": "agendamento_criado"})

        elif intent == "AGENDAR_COM_PREFERENCIA":
            preferencias = ai_manager.extrair_preferencias(corpo_mensagem_original)
            horarios = ai_manager.encontrar_horarios_disponiveis(preferencias)
            cache.set(cache_key, horarios, 600)
            resposta_ia = ai_manager.gerar_resposta_com_horarios(paciente.nome_completo, horarios)
            responder_paciente_via_whatsapp(paciente.contato_telefone, resposta_ia)
            return Response({"status": "horarios_enviados"})

        elif intent == "AGENDAR":
            resposta_ia = ai_manager.gerar_pergunta_preferencia(paciente.nome_completo)
            responder_paciente_via_whatsapp(paciente.contato_telefone, resposta_ia)
            return Response({"status": "aguardando_preferencia"})
        
        elif intent == "SAUDACAO":
            resposta_ia = f"Olá, {paciente.nome_completo.split(' ')[0]}, tudo bem? Como posso te ajudar hoje?"
            responder_paciente_via_whatsapp(paciente.contato_telefone, resposta_ia)
            return Response({"status": "saudacao_respondida"})

        elif intent in ['solicitar_receita', 'solicitar_atestado', 'solicitar_recibo']:
            resposta_ia = ai_manager.registrar_solicitacao_paciente(intent, conta, paciente)
            responder_paciente_via_whatsapp(paciente.contato_telefone, resposta_ia)
            return Response({"status": "solicitacao_registrada"})

        elif intent == "DESCONHECIDO":
            resposta_ia = "Não tenho certeza de como responder a isso. Deseja que eu encaminhe sua mensagem para um de nossos atendentes?"
            responder_paciente_via_whatsapp(paciente.contato_telefone, resposta_ia)
            return Response({"status": "encaminhado_humano"})

        else: # FAQ
            resposta_ia = ai_manager.buscar_e_gerar_resposta_faq(intent, conta)
            responder_paciente_via_whatsapp(paciente.contato_telefone, resposta_ia)
            return Response({"status": "faq_respondido"})

    def handle_novo_contato(self, request, conta, remetente_full, corpo_mensagem_original, intent, ai_manager):
        print(f"--> Ação: Lidando com novo contato: {remetente_full} | Intenção: {intent}")
        remetente_num = ''.join(filter(str.isdigit, remetente_full))
        cache_key_state = f"novo_contato_state_{remetente_num}"
        cache_key_data = f"novo_contato_data_{remetente_num}"
        estado_conversa = cache.get(cache_key_state)
        dados_conversa = cache.get(cache_key_data) or {}
        
        if estado_conversa == 'AWAITING_NAME':
            novo_paciente, created = Paciente.objects.get_or_create(
                conta=conta, contato_telefone=remetente_num,
                defaults={'nome_completo': corpo_mensagem_original, 'cadastrado_por': conta.proprietario}
            )
            horario_escolhido_utc = dados_conversa.get('horario_escolhido')
            Agendamento.objects.create(
                paciente=novo_paciente, profissional=conta.proprietario, titulo="Primeira consulta",
                data_hora_inicio=horario_escolhido_utc, data_hora_fim=horario_escolhido_utc + timedelta(hours=1), status='Confirmado'
            )
            data_local_formatada = timezone.localtime(horario_escolhido_utc).strftime('%A, %d de %B às %H:%M')
            resposta_ia = f"Perfeito, {novo_paciente.nome_completo.split(' ')[0]}! Seu primeiro agendamento para {data_local_formatada} está confirmado. Estamos ansiosos para te receber!"
            responder_paciente_via_whatsapp(remetente_full, resposta_ia)
            cache.delete(cache_key_state)
            cache.delete(cache_key_data)
            return Response({"status": "novo_paciente_agendado"})

        if intent == "ESCOLHEU_HORARIO" and dados_conversa.get('horarios_oferecidos'):
            horario_escolhido = ai_manager.extrair_horario_escolhido(corpo_mensagem_original, dados_conversa['horarios_oferecidos'])
            if horario_escolhido:
                dados_conversa['horario_escolhido'] = horario_escolhido
                cache.set(cache_key_data, dados_conversa, 600)
                cache.set(cache_key_state, 'AWAITING_NAME', 600)
                resposta_ia = ai_manager.gerar_pergunta_nome_completo()
                responder_paciente_via_whatsapp(remetente_full, resposta_ia)
                return Response({"status": "aguardando_nome"})

        elif intent in ["AGENDAR", "AGENDAR_COM_PREFERENCIA"]:
            preferencias = ai_manager.extrair_preferencias(corpo_mensagem_original)
            horarios = ai_manager.encontrar_horarios_disponiveis(preferencias)
            dados_conversa['horarios_oferecidos'] = horarios
            cache.set(cache_key_data, dados_conversa, 600)
            resposta_ia = ai_manager.gerar_resposta_com_horarios("você", horarios)
            responder_paciente_via_whatsapp(remetente_full, resposta_ia)
            return Response({"status": "horarios_enviados_novo_contato"})
        
        # Para qualquer outra intenção (SAUDACAO, FAQ, etc.), um novo contato é convidado a agendar.
        resposta_padrao = f"Olá! Sou a assistente virtual de {conta.nome_conta}. Como posso te ajudar a agendar sua primeira consulta?"
        responder_paciente_via_whatsapp(remetente_full, resposta_padrao)
        return Response({"status": "novo_contato_info"})

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