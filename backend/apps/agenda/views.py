# backend/apps/agenda/views.py

import os
import traceback
from google import genai
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta, datetime
from django.core.cache import cache
from rest_framework import permissions, viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from django.shortcuts import get_object_or_404
from django.db.models import Sum
import re

from apps.users.models import Paciente, Conta, Assinatura
from .ia_manager import GeminiAIManager
from .models import Agendamento, HorarioTrabalho, ExcecaoHorario, FeedbackNPS
from .serializers import AgendamentoSerializer, HorarioTrabalhoSerializer, ExcecaoHorarioSerializer
from apps.financas.models import Transacao

# --- MODO DE SIMULAÇÃO ---
from django.conf import settings

def responder_paciente_via_whatsapp(numero_destinatario, mensagem):
    if settings.DEBUG:
        print("\n" + "*"*10 + " MODO SIMULAÇÃO (DEBUG) " + "*"*10)
        print(f"--> Destinatário: {numero_destinatario}")
        print(f"--> Mensagem que seria enviada:\n{mensagem}")
        print("*"*42 + "\n")
        return True

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
        user = self.request.user
        assinatura = user.conta.assinatura
        if assinatura.plano.nome == 'PREMIUM' and user.funcao == 'profissional':
            return Agendamento.objects.filter(profissional=user)
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
        return Agendamento.objects.filter(paciente__pk=paciente_pk, paciente__conta=self.request.user.conta)

class ConfirmarAgendamentoView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request, token, *args, **kwargs):
        agendamento = get_object_or_404(Agendamento, token_confirmacao=token)
        agendamento.status = 'Confirmado'
        agendamento.save()
        html_response = """
        <html><head><title>Confirmação de Consulta</title><style>body { font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f0f2f5; } .card { background-color: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; } h1 { color: #2ecc71; }</style></head><body><div class="card"><h1>✅ Presença Confirmada!</h1><p>Sua consulta foi confirmada com sucesso.</p><p>Agradecemos a sua colaboração.</p></div></body></html>
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
            
            paciente, is_new_contact = Paciente.objects.get_or_create(
                conta=conta, 
                contato_telefone__contains=remetente_num,
                defaults={'cadastrado_por': conta.proprietario, 'nome_completo': 'Novo Contato'}
            )

            ai_manager = GeminiAIManager(profissional=conta.proprietario)

            if paciente and paciente.conversation_state and paciente.conversation_state.startswith('AWAITING_NPS_'):
                return self.handle_nps_response(paciente, corpo_mensagem_original)

            if paciente:
                agendamento_pendente = Agendamento.objects.filter(
                    paciente=paciente, status__in=['Agendado'], 
                    data_hora_inicio__gte=timezone.now()
                ).order_by('data_hora_inicio').first()
                if agendamento_pendente and corpo_mensagem_original.upper() in ['SIM', 'NÃO', 'REAGENDAR']:
                    return self.handle_lembrete_response(agendamento_pendente, corpo_mensagem_original.upper(), ai_manager)

            if paciente and paciente.onboarding_step:
                return self.handle_onboarding(paciente, corpo_mensagem_original, ai_manager)
            
            intencao = ai_manager.identificar_intencao_geral(corpo_mensagem_original, conta)
            print(f"--> Intenção da IA Identificada: {intencao}")
            
            return self.handle_paciente_existente(paciente, corpo_mensagem_original, intencao, ai_manager)

        except Conta.DoesNotExist:
            print(f"--> Erro Crítico: Nenhum profissional/conta associado ao número de destino {destinatario_num}")
            return Response({"status": "conta_nao_encontrada"})
        except Exception as e:
            traceback.print_exc()
            return Response({"status": "erro_geral", "mensagem": str(e)}, status=500)

    def handle_nps_response(self, paciente, corpo_mensagem):
        # (Seu código original aqui, sem alterações)
        try:
            nota = int(re.search(r'\d+', corpo_mensagem).group())
            if 0 <= nota <= 10:
                agendamento_id = paciente.conversation_state.split('_')[-1]
                agendamento = Agendamento.objects.get(id=agendamento_id)
                FeedbackNPS.objects.create(paciente=paciente, profissional=agendamento.profissional, agendamento=agendamento, nota=nota)
                paciente.conversation_state = None
                paciente.save()
                resposta_ia = "Muito obrigado pelo seu feedback!"
                responder_paciente_via_whatsapp(paciente.contato_telefone, resposta_ia)
                return Response({"status": "nps_recorded"})
        except (ValueError, AttributeError, Agendamento.DoesNotExist):
            resposta_ia = "Não entendi sua resposta. Por favor, responda apenas com um número de 0 a 10."
            responder_paciente_via_whatsapp(paciente.contato_telefone, resposta_ia)
            return Response({"status": "nps_invalid_response"})
        return Response({"status": "nps_error"})

    def handle_lembrete_response(self, agendamento, resposta, ai_manager):
        # (Seu código original aqui, sem alterações)
        if resposta == 'SIM':
            agendamento.status = 'Confirmado'
            agendamento.save()
            responder_paciente_via_whatsapp(agendamento.paciente.contato_telefone, "Obrigado por confirmar! Sua consulta está garantida.")
            return Response({"status": "confirmado"})
        if resposta in ['NÃO', 'REAGENDAR']:
            agendamento.status = 'Cancelado'
            agendamento.save()
            return self.handle_paciente_existente(agendamento.paciente, "gostaria de agendar", "AGENDAR", ai_manager)
        return Response({"status": "lembrete_error"})

    def handle_onboarding(self, paciente, corpo_mensagem, ai_manager):
        if paciente.onboarding_step == 'AWAITING_NAME':
            # MELHORIA: Remove "Meu nome é" se o paciente incluir na resposta
            nome_limpo = re.sub(r'^(meu nome é|me chamo)\s*', '', corpo_mensagem, flags=re.IGNORECASE).strip()
            paciente.nome_completo = nome_limpo
            paciente.onboarding_step = 'AWAITING_DETAILS'
            paciente.save()
            resposta_ia = ai_manager.gerar_pergunta_onboarding(paciente.nome_completo.split(' ')[0])
            responder_paciente_via_whatsapp(paciente.contato_telefone, resposta_ia)
            return Response({"status": "onboarding_asked_details"})

        elif paciente.onboarding_step == 'AWAITING_DETAILS':
            dados = ai_manager.extrair_dados_onboarding(corpo_mensagem)
            if dados.get('cpf'):
                paciente.cpf = dados['cpf']
            if dados.get('data_nascimento'):
                try:
                    data_nasc = datetime.strptime(dados['data_nascimento'], '%d/%m/%Y').strftime('%Y-%m-%d')
                    paciente.data_nascimento = data_nasc
                except ValueError:
                    pass
            paciente.onboarding_step = None
            paciente.save()
            resposta_ia = "Obrigado! Suas informações foram salvas com sucesso. Se precisar de mais alguma coisa, é só chamar!"
            responder_paciente_via_whatsapp(paciente.contato_telefone, resposta_ia)
            return Response({"status": "onboarding_complete"})
        return Response({"status": "onboarding_unknown_step"})

    def handle_paciente_existente(self, paciente, corpo_mensagem_original, intent, ai_manager):
        print(f"--> Ação: Lidando com paciente: {paciente.nome_completo or 'Novo Contato'} | Intenção: {intent}")
        conta = paciente.conta
        
        try:
            assinatura = conta.assinatura
            if not assinatura.ativa or assinatura.plano.limite_mensagens_ia == 0:
                return Response({"status": "plano_incompativel"})
        except Assinatura.DoesNotExist:
            return Response({"status": "sem_assinatura"})

        cache_key = f"horarios_oferecidos_{paciente.id}"
        horarios_oferecidos_cache = cache.get(cache_key)

        if intent == "ESCOLHEU_HORARIO":
            horario_escolhido_utc = None
            if horarios_oferecidos_cache:
                horario_escolhido_utc = ai_manager.extrair_horario_escolhido(corpo_mensagem_original, horarios_oferecidos_cache)
            
            if horario_escolhido_utc:
                Agendamento.objects.create(paciente=paciente, profissional=conta.proprietario, titulo="Consulta agendada pela IA", data_hora_inicio=horario_escolhido_utc, data_hora_fim=horario_escolhido_utc + timedelta(hours=1), status='Confirmado')
                
                if not paciente.nome_completo or "Novo Contato" in paciente.nome_completo:
                    paciente.onboarding_step = 'AWAITING_NAME'
                    paciente.save()
                    resposta_ia = ai_manager.gerar_pergunta_nome_completo()
                else:
                    data_local_formatada = timezone.localtime(horario_escolhido_utc).strftime('%A, %d de %B às %H:%M').capitalize()
                    resposta_ia = f"Perfeito, {paciente.nome_completo.split(' ')[0]}! Seu agendamento para {data_local_formatada} está confirmado. Até lá!"
                
                responder_paciente_via_whatsapp(paciente.contato_telefone, resposta_ia)
                cache.delete(cache_key)
                return Response({"status": "agendamento_criado"})
            else:
                # MELHORIA: Se não escolheu um horário válido, trata como uma nova preferência
                intent = "AGENDAR_COM_PREFERENCIA"

        if intent == "AGENDAR_COM_PREFERENCIA":
            preferencias = ai_manager.extrair_preferencias(corpo_mensagem_original)
            horarios = ai_manager.encontrar_horarios_disponiveis(preferencias)
            cache.set(cache_key, horarios, 600)
            nome_para_resposta = paciente.nome_completo.split(' ')[0] if paciente.nome_completo and "Novo Contato" not in paciente.nome_completo else "você"
            resposta_ia = ai_manager.gerar_resposta_com_horarios(nome_para_resposta, horarios)
            responder_paciente_via_whatsapp(paciente.contato_telefone, resposta_ia)
            return Response({"status": "horarios_enviados"})

        elif intent == "AGENDAR":
            nome_para_resposta = paciente.nome_completo.split(' ')[0] if paciente.nome_completo and "Novo Contato" not in paciente.nome_completo else "você"
            resposta_ia = ai_manager.gerar_pergunta_preferencia(nome_para_resposta)
            responder_paciente_via_whatsapp(paciente.contato_telefone, resposta_ia)
            return Response({"status": "aguardando_preferencia"})
        
        elif intent == "SAUDACAO":
            nome_para_resposta = paciente.nome_completo.split(' ')[0] if paciente.nome_completo and "Novo Contato" not in paciente.nome_completo else "tudo bem?"
            resposta_ia = f"Olá, {nome_para_resposta}! Sou a assistente virtual do(a) {conta.nome_conta}. Como posso te ajudar hoje?"
            responder_paciente_via_whatsapp(paciente.contato_telefone, resposta_ia)
            return Response({"status": "saudacao_respondida"})

        elif intent == "VERIFICAR_PENDENCIAS":
            if not paciente.nome_completo or "Novo Contato" in paciente.nome_completo:
                 resposta_ia = "Para verificar informações financeiras, primeiro preciso que você se identifique. Por favor, me informe seu nome completo."
                 paciente.onboarding_step = 'AWAITING_NAME'
                 paciente.save()
            else:
                resposta_ia = ai_manager.buscar_e_responder_pendencias(paciente)
            responder_paciente_via_whatsapp(paciente.contato_telefone, resposta_ia)
            return Response({"status": "pendencias_verificadas"})

        elif intent in ['solicitar_receita', 'solicitar_atestado', 'solicitar_recibo']:
            if not paciente.nome_completo or "Novo Contato" in paciente.nome_completo:
                resposta_ia = "Para solicitar documentos, primeiro preciso que você se identifique. Por favor, me informe seu nome completo."
                paciente.onboarding_step = 'AWAITING_NAME'
                paciente.save()
            else:
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
            
class HorarioTrabalhoViewSet(viewsets.ModelViewSet):
    # (Seu código original aqui, sem alterações)
    serializer_class = HorarioTrabalhoSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return HorarioTrabalho.objects.filter(profissional=self.request.user)
    def perform_create(self, serializer):
        serializer.save(profissional=self.request.user)

class ExcecaoHorarioViewSet(viewsets.ModelViewSet):
    # (Seu código original aqui, sem alterações)
    serializer_class = ExcecaoHorarioSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return ExcecaoHorario.objects.filter(profissional=self.request.user, data__gte=timezone.localdate())
    def perform_create(self, serializer):
        serializer.save(profissional=self.request.user)