import os
import google.generativeai as genai
from apps.users.models import Profissional, Conta, ItemFAQ, PerfilClinica, Paciente
from apps.financas.models import Servico, Transacao
from apps.agenda.models import Agendamento, HorarioTrabalho, ExcecaoHorario
from apps.solicitacoes.models import Solicitacao
from datetime import timedelta, time, datetime, timezone
import json
from django.utils import timezone as django_timezone
from twilio.rest import Client
import re # <-- Importe a biblioteca de expressões regulares

# (Mantenha a configuração da API da Gemini)
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

    def identificar_intencao_geral(self, mensagem_paciente: str, conta: Conta):
        """
        Primeiro passo: Tenta classificar a mensagem em uma intenção de alto nível.
        """
        itens_faq = ItemFAQ.objects.filter(conta=conta)
        intencoes_cadastradas = "\n".join([f"- {item.intencao_chave}: {item.perguntas_exemplo}" for item in itens_faq])

        prompt = f"""
        Analise a mensagem do paciente e classifique-a em uma das intenções abaixo.
        Se for sobre agendamento, use as intenções de agendamento.
        Se corresponder a uma das intenções do FAQ, use a chave da intenção.
        Se for uma pergunta sobre valores pendentes, use a intenção de finanças.

        Intenções de Agendamento:
        - SAUDACAO: Se for apenas um cumprimento ou uma mensagem genérica sem um pedido claro. (Ex: "oi, bom dia", "olá", "tudo bem?")
        - AGENDAR: Se o paciente quer marcar uma consulta, mas não especificou um dia ou período.
        - AGENDAR_COM_PREFERENCIA: Se o paciente quer marcar e JÁ ESPECIFICOU um dia ou período.
        - ESCOLHEU_HORARIO: Se a mensagem do paciente corresponde claramente a um dos horários específicos que foram oferecidos.

        Intenções do FAQ da Clínica:
        {intencoes_cadastradas}
        
        Intenção de Finanças:
        - VERIFICAR_PENDENCIAS: Se o paciente está perguntando sobre débitos ou pagamentos pendentes. (Ex: "tenho algo para pagar?", "estou devendo alguma consulta?", "qual o valor em aberto?")

        Se não se encaixar em nada, responda "DESCONHECIDO".

        Mensagem: "{mensagem_paciente}"
        Sua Resposta: 
        """
        response = self.model.generate_content(prompt)
        return response.text.strip()
    
    # --- NOVA FUNÇÃO ---
    def gerar_pergunta_onboarding(self, nome_paciente: str):
        """ Gera a mensagem para solicitar os dados de onboarding. """
        prompt = f"""
        Você é uma secretária virtual. O novo paciente, {nome_paciente}, acabou de ter sua primeira consulta agendada.
        Sua tarefa é gerar uma mensagem amigável para adiantar o cadastro dele, pedindo o CPF e a data de nascimento.

        Exemplo de resposta:
        "Perfeito, {nome_paciente}! Seu agendamento está confirmado. Para agilizar seu atendimento no dia, você poderia me informar seu CPF e data de nascimento, por favor? (Ex: 123.456.789-10 e 25/12/1990)"
        """
        response = self.model.generate_content(prompt)
        return response.text.strip()

    # --- NOVA FUNÇÃO ---
    def extrair_dados_onboarding(self, mensagem: str):
        """ Extrai CPF e Data de Nascimento da mensagem do paciente. """
        cpf_pattern = r'\d{3}\.?\d{3}\.?\d{3}-?\d{2}'
        data_pattern = r'\d{2}/\d{2}/\d{4}'
        
        cpf_match = re.search(cpf_pattern, mensagem)
        data_match = re.search(data_pattern, mensagem)
        
        cpf = cpf_match.group(0) if cpf_match else None
        data_nascimento = data_match.group(0) if data_match else None
        
        return {'cpf': cpf, 'data_nascimento': data_nascimento}
        
    # --- NOVA FUNÇÃO ---
    def buscar_e_responder_pendencias(self, paciente: Paciente):
        """ Consulta e gera uma resposta sobre as pendências financeiras do paciente. """
        pendencias = Transacao.objects.filter(paciente=paciente, status='pendente')
        
        if not pendencias.exists():
            return f"Verifiquei aqui, {paciente.nome_completo.split(' ')[0]}, e não há nenhum valor pendente em seu nome. Está tudo certo!"

        total_pendente = pendencias.aggregate(total=models.Sum('valor_cobrado'))['total']
        valor_formatado = f"R$ {total_pendente:.2f}".replace('.', ',')

        prompt = f"""
        Você é uma secretária virtual. O paciente {paciente.nome_completo} perguntou sobre seus débitos.
        Você consultou o sistema e encontrou um valor total pendente de {valor_formatado}.
        
        Sua tarefa é formular uma resposta amigável informando o valor pendente. Ofereça ajuda para realizar o pagamento, como enviar um código PIX.
        
        Exemplo de resposta:
        "Olá, {paciente.nome_completo.split(' ')[0]}! Verifiquei no sistema e consta um valor total de {valor_formatado} em aberto. Gostaria que eu enviasse o código PIX para facilitar o pagamento?"
        """
        response = self.model.generate_content(prompt)
        return response.text.strip()
    
    # ...(O restante do arquivo ia_manager.py continua daqui, sem alterações)...
    # Copie e cole o restante do seu arquivo ia_manager.py original abaixo desta linha.
    def buscar_e_gerar_resposta_faq(self, intencao_identificada: str, conta: Conta):
        """
        Busca a resposta no banco de dados, enriquece com dados dinâmicos se necessário,
        e gera uma resposta amigável para o paciente.
        """
        try:
            item_faq = ItemFAQ.objects.get(conta=conta, intencao_chave=intencao_identificada)
            resposta_base = item_faq.resposta
            contexto_dinamico = ""

            # Se a intenção for sobre serviços, busca os serviços cadastrados.
            if intencao_identificada == 'conhecer_servicos':
                servicos = Servico.objects.filter(conta=conta, ativo=True)
                if servicos.exists():
                    lista_servicos = ", ".join([s.nome_servico for s in servicos])
                    contexto_dinamico = f"Aqui estão os serviços que oferecemos: {lista_servicos}."
                else:
                    contexto_dinamico = "Ainda não temos uma lista de serviços cadastrada."

            # Se a intenção for sobre localização, busca dados do perfil e horários.
            elif intencao_identificada == 'localizacao_contato':
                perfil = conta.perfil
                horarios = HorarioTrabalho.objects.filter(profissional__conta=conta, ativo=True).order_by('dia_da_semana')
                
                info_perfil = f"O endereço é {perfil.endereco_completo or '[Endereço não informado]'}. O telefone para contato é {self.profissional.contato_telefone or '[Telefone não informado]'}. O site é {perfil.site_url or '[Site não informado]'}"
                
                if horarios.exists():
                    texto_horarios = " Nosso horário de funcionamento é:"
                    dias_semana = dict(HorarioTrabalho.DIAS_SEMANA)
                    for h in horarios:
                        texto_horarios += f" {dias_semana[h.dia_da_semana]} das {h.hora_inicio.strftime('%H:%M')} às {h.hora_fim.strftime('%H:%M')};"
                    contexto_dinamico = info_perfil + texto_horarios
                else:
                    contexto_dinamico = info_perfil + ". O horário de funcionamento não foi cadastrado."

            # Se a intenção for sobre profissionais, busca a equipe da conta.
            elif intencao_identificada == 'conhecer_profissionais':
                profissionais = Profissional.objects.filter(conta=conta, is_active=True)
                lista_profissionais = ", ".join([p.nome_completo for p in profissionais])
                contexto_dinamico = f"Nossa equipe é composta por: {lista_profissionais}."

            # Monta o prompt final para a IA
            prompt = f"""
            Você é uma secretária virtual. Um paciente fez uma pergunta e esta é a informação correta para respondê-lo.
            
            **Resposta Padrão Cadastrada:**
            "{resposta_base}"

            **Informações Adicionais do Sistema (use se for relevante):**
            {contexto_dinamico}

            Sua tarefa é formular uma resposta amigável e natural para o paciente. Se houver informações adicionais, integre-as de forma fluida à resposta padrão.
            Não inclua os colchetes como '[Endereço não informado]', apenas omita a informação se ela não existir.
            """
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except ItemFAQ.DoesNotExist:
            return "Peço desculpas, mas não encontrei uma resposta para sua pergunta. Posso tentar ajudar com outra coisa?"
        except Exception as e:
            print(f"ERRO inesperado ao buscar resposta do FAQ: {e}")
            return "Não consegui processar sua solicitação no momento. Por favor, tente novamente."

    def analisar_mensagem_paciente(self, mensagem_paciente: str, horarios_oferecidos: list = None):
        horarios_ofertados_str = "Nenhum horário foi oferecido ainda."
        if horarios_oferecidos:
            horarios_formatados = [
                f"'{django_timezone.localtime(h).strftime('%A, dia %d, às %H:%M')}'"
                for h in horarios_oferecidos
            ]
            horarios_ofertados_str = f"Os seguintes horários foram oferecidos ao paciente: {', '.join(horarios_formatados)}"

        prompt = f"""
        Analise a mensagem do paciente e determine sua intenção principal, considerando o contexto da conversa.
        Responda APENAS com um JSON contendo a chave "intent".

        Contexto da conversa:
        {horarios_ofertados_str}

        As intenções possíveis são:
        - "SAUDACAO": Se for apenas um cumprimento ou uma mensagem genérica sem um pedido claro. (Ex: "oi, bom dia", "olá", "tudo bem?")
        - "AGENDAR": Se o paciente quer marcar uma consulta, mas não especificou um dia ou período.
        - "AGENDAR_COM_PREFERENCIA": Se o paciente quer marcar e JÁ ESPECIFICOU um dia ou período.
        - "ESCOLHEU_HORARIO": Se a mensagem do paciente corresponde claramente a um dos horários específicos que foram oferecidos.
        - "DUVIDA": Se o paciente está fazendo uma pergunta geral.

        Mensagem do paciente: "{mensagem_paciente}"
        """
        response = self.model.generate_content(prompt)
        try:
            cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
            return json.loads(cleaned_response)
        except (json.JSONDecodeError, AttributeError):
            return {"intent": "DESCONHECIDO"}

    def gerar_pergunta_nome_completo(self):
        prompt = """
        Você é uma secretária virtual. Um novo paciente acaba de confirmar um horário para sua primeira consulta.
        Sua tarefa é pedir, de forma amigável, o nome completo dele para finalizar o agendamento.

        Exemplo de resposta:
        "Ótimo! Para finalizar o seu agendamento, por favor, me informe o seu nome completo."
        """
        response = self.model.generate_content(prompt)
        return response.text.strip()

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

    def extrair_horario_escolhido(self, mensagem_paciente: str, horarios_oferecidos: list):
        """
        A partir de uma lista de horários oferecidos, identifica qual deles o paciente escolheu.
        """
        horarios_formatados = [
            f"'{django_timezone.localtime(h).strftime('%A, dia %d, às %H:%M')}'" 
            for h in horarios_oferecidos
        ]
        
        prompt = f"""
        Analise a mensagem do paciente e determine qual dos horários da lista ele escolheu.
        Responda APENAS com o horário escolhido, exatamente como ele aparece na lista.
        Se a mensagem do paciente não corresponder a nenhum horário, responda com "NENHUM".

        Lista de horários oferecidos:
        {", ".join(horarios_formatados)}

        Mensagem do paciente: "{mensagem_paciente}"
        """
        response = self.model.generate_content(prompt)
        escolha = response.text.strip().replace("'", "")

        if escolha == "NENHUM":
            return None

        # Encontra o objeto datetime original que corresponde à string escolhida
        for horario_obj in horarios_oferecidos:
            if django_timezone.localtime(horario_obj).strftime('%A, dia %d, às %H:%M') == escolha:
                return horario_obj
        
        return None

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
        if not horarios:
            return f"Olá, {nome_paciente}! Puxa, não encontrei horários disponíveis com essa preferência para os próximos 30 dias. Gostaria de tentar outro dia ou período? Se preferir, posso deixar seu nome em nossa lista de espera."

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

    def registrar_solicitacao_paciente(self, intencao: str, conta: Conta, paciente: 'Paciente'):
        """
        Registra uma nova solicitação no banco de dados e retorna uma mensagem de confirmação.
        """
        mapa_intencao_tipo = {
            'solicitar_receita': 'RECEITA',
            'solicitar_atestado': 'ATESTADO',
            'solicitar_recibo': 'RECIBO'
        }
        
        tipo = mapa_intencao_tipo.get(intencao)
        if not tipo:
            return "Não entendi qual documento você precisa. Pode especificar?"

        # Cria a solicitação no banco de dados
        Solicitacao.objects.create(
            conta=conta,
            paciente=paciente,
            profissional_atribuido=conta.proprietario, # Atribui ao proprietário por padrão
            tipo_solicitacao=tipo
        )

        # Gera uma resposta de confirmação amigável
        prompt = f"""
        Você é uma secretária virtual. O paciente {paciente.nome_completo} acabou de solicitar um documento do tipo '{tipo}'.
        Sua tarefa é gerar uma resposta curta e amigável confirmando que a solicitação foi registrada e será encaminhada ao profissional responsável.
        
        Exemplo: "Registrado! Sua solicitação de {tipo.lower()} foi encaminhada para o(a) Dr(a). {conta.proprietario.nome_completo}. Avisaremos assim que estiver pronto!"
        """
        response = self.model.generate_content(prompt)
        return response.text.strip()