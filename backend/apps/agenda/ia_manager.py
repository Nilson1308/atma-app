import os
import google.generativeai as genai
from apps.users.models import Profissional
from apps.agenda.models import Agendamento, HorarioTrabalho, ExcecaoHorario
from datetime import timedelta, time, datetime, timezone
import json
from django.utils import timezone as django_timezone
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

    def analisar_mensagem_paciente(self, mensagem_paciente: str):
        prompt = f"""
        Analise a mensagem do paciente e determine sua intenção principal.
        Responda APENAS com um JSON contendo a chave "intent".

        As intenções possíveis são:
        - "AGENDAR": Se o paciente quer marcar uma consulta, mas não especificou um dia ou período. (Ex: "Quero marcar uma consulta", "Gostaria de um horário")
        - "AGENDAR_COM_PREFERENCIA": Se o paciente quer marcar e JÁ ESPECIFICOU um dia ou período. (Ex: "Tem horário para terça à tarde?", "Pode ser na sexta de manhã?", "Nenhum desses serve, tem na segunda?")
        - "ESCOLHEU_HORARIO": Se o paciente está confirmando um horário específico que foi oferecido. (Ex: "Pode ser às 10h", "ok, confirmado para as 9h", "Gostei do primeiro horário")
        - "DUVIDA": Se o paciente está fazendo uma pergunta geral que não seja sobre agendamento.

        Mensagem do paciente: "{mensagem_paciente}"
        """
        response = self.model.generate_content(prompt)
        try:
            cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
            return json.loads(cleaned_response)
        except (json.JSONDecodeError, AttributeError):
            return {"intent": "DESCONHECIDO"}

    def gerar_pergunta_preferencia(self, nome_paciente: str):
        prompt = f"""
        Você é uma secretária virtual para {self.profissional.nome_completo}.
        Sua tarefa é responder a um paciente chamado {nome_paciente} que pediu para agendar uma consulta.
        Responda de forma amigável e pergunte qual o dia da semana ou período (manhã/tarde) de sua preferência para o agendamento.

        Exemplo de resposta:
        "Olá, {nome_paciente}, tudo bem? Claro! Para te ajudar a encontrar o melhor horário, você tem alguma preferência de dia da semana ou período (manhã ou tarde)?"
        """
        response = self.model.generate_content(prompt)
        return response.text.strip()

    def extrair_preferencias(self, mensagem_paciente: str):
        prompt = f"""
        Analise a mensagem do paciente e extraia o dia da semana, o período (manhã, tarde, noite) e um horário específico, se houver.
        Responda APENAS com um JSON contendo as chaves "dia_semana", "periodo" e "hora".
        - "dia_semana": número de 0 (Segunda) a 6 (Domingo). Se não for mencionado, use null.
        - "periodo": "manha", "tarde" ou "noite". Se não for mencionado, use null.
        - "hora": "HH:MM". Se não for mencionado, use null.

        Exemplos:
        - Mensagem: "Pode ser na quarta à tarde" -> {{"dia_semana": 2, "periodo": "tarde", "hora": null}}
        - Mensagem: "Gostaria de uma sexta-feira às 10h" -> {{"dia_semana": 4, "periodo": null, "hora": "10:00"}}
        - Mensagem: "qualquer um" -> {{"dia_semana": null, "periodo": null, "hora": null}}
        - Mensagem: "às 18h" -> {{"dia_semana": null, "periodo": null, "hora": "18:00"}}

        Mensagem do paciente: "{mensagem_paciente}"
        """
        response = self.model.generate_content(prompt)
        try:
            cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
            return json.loads(cleaned_response)
        except (json.JSONDecodeError, AttributeError):
            return {"dia_semana": None, "periodo": None, "hora": None}

    def encontrar_horarios_disponiveis(self, preferencias=None):
        """
        Verifica a agenda do profissional e retorna os próximos 3 horários livres,
        respeitando os horários de trabalho e exceções cadastrados.
        """
        agora_local = django_timezone.localtime(django_timezone.now())
        horarios_encontrados = []

        periodos = {
            "manha": (time(8, 0), time(12, 0)),
            "tarde": (time(12, 0), time(18, 0)),
            "noite": (time(18, 0), time(21, 0)),
        }

        dia_preferido = preferencias.get('dia_semana') if preferencias else None
        periodo_preferido = preferencias.get('periodo') if preferencias else None
        hora_preferida_str = preferencias.get('hora') if preferencias else None

        for dia_delta in range(30):
            data_atual = agora_local.date() + timedelta(days=dia_delta)
            dia_da_semana = data_atual.weekday()

            if dia_preferido is not None and dia_da_semana != dia_preferido:
                continue

            horario_inicio_trabalho = None
            horario_fim_trabalho = None

            try:
                excecao = ExcecaoHorario.objects.get(profissional=self.profissional, data=data_atual)
                if excecao.dia_inteiro:
                    continue
                else:
                    horario_inicio_trabalho = excecao.hora_inicio
                    horario_fim_trabalho = excecao.hora_fim
            except ExcecaoHorario.DoesNotExist:
                try:
                    horario_padrao = HorarioTrabalho.objects.get(
                        profissional=self.profissional,
                        dia_da_semana=dia_da_semana,
                        ativo=True
                    )
                    horario_inicio_trabalho = horario_padrao.hora_inicio
                    horario_fim_trabalho = horario_padrao.hora_fim
                except HorarioTrabalho.DoesNotExist:
                    continue

            if not horario_inicio_trabalho or not horario_fim_trabalho:
                continue

            # Se uma hora específica foi pedida, cria uma lista com apenas esse horário para verificar
            horas_para_verificar = []
            if hora_preferida_str:
                try:
                    hora_proposta_time = datetime.strptime(hora_preferida_str, '%H:%M').time()
                    if hora_proposta_time >= horario_inicio_trabalho and hora_proposta_time < horario_fim_trabalho:
                        horas_para_verificar.append(hora_proposta_time)
                except ValueError:
                    pass # Ignora hora mal formatada
            else:
                # Se não tem hora específica, continua com a lógica de períodos
                hora_inicio_busca = horario_inicio_trabalho
                hora_fim_busca = horario_fim_trabalho
                
                if periodo_preferido and periodo_preferido in periodos:
                    hora_inicio_busca = max(horario_inicio_trabalho, periodos[periodo_preferido][0])
                    hora_fim_busca = min(horario_fim_trabalho, periodos[periodo_preferido][1])

                hora_atual = datetime.combine(data_atual, hora_inicio_busca)
                hora_limite = datetime.combine(data_atual, hora_fim_busca)
                while hora_atual < hora_limite:
                    horas_para_verificar.append(hora_atual.time())
                    hora_atual += timedelta(hours=1)
            
            # Itera sobre os horários candidatos (seja um específico ou vários de um período)
            for hora_time in horas_para_verificar:
                hora_proposta = datetime.combine(data_atual, hora_time)
                horario_proposto_local = django_timezone.make_aware(hora_proposta)

                if horario_proposto_local > agora_local:
                    horario_proposto_utc_fim = (horario_proposto_local + timedelta(hours=1)).astimezone(timezone.utc)

                    conflito = Agendamento.objects.filter(
                        profissional=self.profissional,
                        data_hora_inicio__lt=horario_proposto_utc_fim,
                        data_hora_fim__gt=horario_proposto_local.astimezone(timezone.utc)
                    ).exists()

                    if not conflito:
                        horarios_encontrados.append(horario_proposto_local.astimezone(timezone.utc))
                        if len(horarios_encontrados) >= 3:
                            return horarios_encontrados

        return horarios_encontrados

    def gerar_resposta_com_horarios(self, nome_paciente: str, horarios=None):
        # --- PEQUENO AJUSTE AQUI ---
        if not horarios:
            return f"Olá, {nome_paciente}! Puxa, não encontrei horários disponíveis com essa preferência. Gostaria de tentar outro dia ou período?"

        horarios_formatados = [django_timezone.localtime(h).strftime('%A, dia %d, às %H:%M') for h in horarios]
        texto_horarios = "\n".join(f"• {h}" for h in horarios_formatados)

        prompt = f"""
        Você é uma secretária virtual para {self.profissional.nome_completo}. Sua tarefa é responder a um paciente chamado {nome_paciente}.

        **Instruções para a resposta:**
        - **Tom de voz:** Amigável e prestativo.
        - **Apresente os horários:** Diga que encontrou alguns horários e apresente a lista.
        - **Chamada para ação:** Pergunte qual opção é a melhor para ele.

        **Horários disponíveis:**
        {texto_horarios}

        **Exemplo de resposta:**
        "Perfeito, {nome_paciente}! Verifiquei aqui e encontrei os seguintes horários para você:
        {texto_horarios}
        Qual dessas opções fica melhor?"

        Agora, escreva a resposta final para o paciente.
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Erro ao gerar resposta com a Gemini: {e}")
            return "Encontrei alguns horários. Poderia, por favor, ligar para confirmarmos?"
