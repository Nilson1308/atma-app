import os
import google.generativeai as genai
from apps.users.models import Profissional
from apps.agenda.models import Agendamento
from datetime import timedelta, time, datetime
from django.utils import timezone
from twilio.rest import Client

# Configura a API da Gemini
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class GeminiAIManager:
    """
    Esta classe gere toda a comunicação com a API da Gemini.
    """
    def __init__(self, profissional: Profissional):
        self.profissional = profissional
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest')

    def interpretar_mensagem_paciente(self, mensagem_paciente: str):
        prompt = f"""
        Você é uma secretária virtual para {self.profissional.nome_completo}, um(a) profissional de saúde.
        Um paciente enviou a seguinte mensagem via WhatsApp: "{mensagem_paciente}"

        A sua tarefa é analisar esta mensagem e determinar a intenção do paciente.
        Responda com APENAS uma das seguintes palavras-chave:
        - AGENDAR (se o paciente quiser marcar uma nova consulta)
        - DUVIDA (se o paciente estiver a fazer uma pergunta geral)
        - DESCONHECIDO (se a intenção não for clara ou não se enquadrar nas outras)
        """
        try:
            response = self.model.generate_content(prompt)
            intent = response.text.strip().upper()
            print(f"Intenção da IA: {intent}")
            return intent
        except Exception as e:
            print(f"Erro ao comunicar com a Gemini API: {e}")
            return "ERRO_API"

    def encontrar_horarios_disponiveis(self):
        """
        Verifica a agenda do profissional e retorna os próximos 3 horários livres,
        respeitando o fuso horário local do projeto.
        """
        agora_local = timezone.localtime(timezone.now())
        horarios_encontrados = []
        
        horario_inicio_trabalho = time(9, 0)
        horario_fim_trabalho = time(18, 0)

        for dia_delta in range(14):
            data_atual = agora_local.date() + timedelta(days=dia_delta)
            
            if data_atual.weekday() >= 5: continue

            for hora in range(horario_inicio_trabalho.hour, horario_fim_trabalho.hour):
                # Cria um datetime "naive" (sem fuso horário)
                horario_proposto_naive = datetime.combine(data_atual, time(hour=hora))
                
                # --- CORREÇÃO APLICADA AQUI ---
                # Usa o método moderno do Django para tornar o datetime "aware" (consciente do fuso horário)
                horario_proposto_local = timezone.make_aware(horario_proposto_naive)

                if horario_proposto_local < agora_local: continue

                horario_proposto_utc_inicio = horario_proposto_local.astimezone(timezone.utc)
                horario_proposto_utc_fim = horario_proposto_utc_inicio + timedelta(hours=1)

                conflito = Agendamento.objects.filter(
                    profissional=self.profissional,
                    data_hora_inicio__lt=horario_proposto_utc_fim,
                    data_hora_fim__gt=horario_proposto_utc_inicio
                ).exists()

                if not conflito:
                    horarios_encontrados.append(horario_proposto_utc_inicio)
                    if len(horarios_encontrados) >= 3:
                        return horarios_encontrados
        
        return horarios_encontrados

    def gerar_resposta_com_horarios(self):
        horarios = self.encontrar_horarios_disponiveis()
        if not horarios:
            return "Peço desculpa, mas parece que não tenho horários disponíveis nos próximos dias."

        horarios_formatados = [timezone.localtime(h).strftime('%A, %d de %B às %H:%M') for h in horarios]
        texto_horarios = "\n".join(f"- {h}" for h in horarios_formatados)

        prompt = f"""
        Você é uma secretária virtual para {self.profissional.nome_completo}.
        Um paciente pediu para agendar uma consulta. Você encontrou os seguintes horários disponíveis:
        {texto_horarios}

        A sua tarefa é escrever uma resposta amigável e clara para o paciente via WhatsApp.
        Apresente-se brevemente como a assistente virtual, ofereça as opções de horário e pergunte qual delas ele prefere.
        Não use placeholders como "[Seu Nome]". Assine a mensagem apenas com "Assistente Virtual Atma".
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Erro ao gerar resposta com a Gemini: {e}")
            return "Encontrei alguns horários. Poderia, por favor, ligar para confirmarmos?"

