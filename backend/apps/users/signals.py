from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Conta, CategoriaFAQ, ItemFAQ, PerfilClinica

# Estrutura de dados com o FAQ Padrão
DEFAULT_FAQ_STRUCTURE = [
    {
        "categoria": "Informações Gerais",
        "itens": [
            {
                "intencao_chave": "conhecer_servicos",
                "perguntas_exemplo": "Quais serviços vocês oferecem?; Quais as especialidades da clínica?; Vocês fazem [tipo de terapia/exame específico]?; Qual o foco de atendimento de vocês?",
                "resposta": "Olá! Oferecemos uma variedade de serviços focados em [Sua Especialidade Principal]. Para ver a lista completa e detalhada, por favor, acesse nosso site: [Link para o Site]. Gostaria de saber sobre algo específico?"
            },
            {
                "intencao_chave": "conhecer_profissionais",
                "perguntas_exemplo": "Quais médicos/terapeutas atendem na clínica?; Quem é o especialista em [área específica]?; Gostaria de saber mais sobre o Dr(a). [Nome do Profissional].",
                "resposta": "Nossa equipe é formada por profissionais qualificados e dedicados. O responsável pelos atendimentos é o(a) [Seu Nome/Nome do Profissional Principal]. Você pode conhecer mais sobre nossa equipe em nosso site: [Link para a página 'Sobre Nós' ou 'Equipe']."
            },
            {
                "intencao_chave": "localizacao_contato",
                "perguntas_exemplo": "Onde fica a clínica?; Qual o endereço de vocês?; Como faço para chegar?; Qual o horário de funcionamento?; Qual o telefone de contato?",
                "resposta": "Estamos localizados em [Seu Endereço Completo]. Nosso horário de funcionamento é de [Seus Dias de Funcionamento], das [Seu Horário de Início] às [Seu Horário de Fim]. Nosso telefone para contato é [Seu Telefone]."
            },
        ]
    },
    {
        "categoria": "Convênios e Pagamentos",
        "itens": [
            {
                "intencao_chave": "verificar_convenios",
                "perguntas_exemplo": "Vocês aceitam o convênio [Nome do Convênio]?; Meu plano [Nome do Plano] tem cobertura?; Como funciona o atendimento por convênio?",
                "resposta": "No momento, atendemos de forma particular. Oferecemos recibo para que você possa solicitar o reembolso junto ao seu plano de saúde, caso ele ofereça essa opção. Como posso ajudar?"
            },
            {
                "intencao_chave": "detalhes_pagamento",
                "perguntas_exemplo": "Posso pagar com cartão de crédito?; Vocês parcelam?; Aceitam Pix?",
                "resposta": "Sim! Aceitamos pagamentos via Pix, dinheiro, cartão de crédito e débito. Se precisar de mais alguma informação, é só perguntar!"
            }
        ]
    },
    {
        "categoria": "Sobre as Consultas",
        "itens": [
            {
                "intencao_chave": "primeira_consulta",
                "perguntas_exemplo": "Como funciona a primeira consulta?; O que eu preciso saber para meu primeiro atendimento?; Vocês estão aceitando novos pacientes?",
                "resposta": "Olá! Sim, estamos aceitando novos pacientes. A primeira consulta é um momento para nos conhecermos melhor, entendermos suas necessidades e definirmos juntos os próximos passos. Ela tem duração de aproximadamente [Duração da Consulta] minutos."
            },
            {
                "intencao_chave": "preparacao_consulta",
                "perguntas_exemplo": "O que preciso levar no dia da consulta?; Preciso levar exames antigos?; É necessário algum preparo, como jejum?",
                "resposta": "Para sua consulta, por favor, traga um documento de identificação. Se tiver exames recentes relacionados ao motivo da consulta, pode trazê-los também. Não é necessário nenhum preparo específico, como jejum."
            }
        ]
    }
]


@receiver(post_save, sender=Conta)
def criar_recursos_padrao_para_conta(sender, instance, created, **kwargs):
    """
    Este sinal é acionado sempre que uma nova Conta é criada.
    Ele irá criar o Perfil e popular o FAQ com os dados padrão.
    """
    if created:
        # Cria o Perfil da Clínica
        PerfilClinica.objects.create(conta=instance)
        print(f"--> Perfil para a conta '{instance.nome_conta}' criado.")

        # Popula o FAQ Padrão
        print(f"--> Nova conta '{instance.nome_conta}' criada. Populando FAQ padrão...")
        for cat_data in DEFAULT_FAQ_STRUCTURE:
            # Cria a categoria
            categoria = CategoriaFAQ.objects.create(
                conta=instance,
                nome=cat_data["categoria"]
            )
            # Cria os itens dentro da categoria
            for item_data in cat_data["itens"]:
                # A CORREÇÃO ESTÁ AQUI (ADICIONADO O RECUO)
                ItemFAQ.objects.create(
                    conta=instance,
                    categoria=categoria,
                    intencao_chave=item_data["intencao_chave"],
                    perguntas_exemplo=item_data["perguntas_exemplo"],
                    resposta=item_data["resposta"]
                )
        print(f"--> FAQ padrão para '{instance.nome_conta}' populado com sucesso!")

@receiver(post_save, sender=Conta)
def popular_faq_padrao(sender, instance, created, **kwargs):
    """
    Este sinal é acionado sempre que uma nova Conta é criada.
    Ele irá popular o FAQ com os dados padrão.
    """
    if created:
        print(f"--> Nova conta '{instance.nome_conta}' criada. Populando FAQ padrão...")
        for cat_data in DEFAULT_FAQ_STRUCTURE:
            # Cria a categoria
            categoria = CategoriaFAQ.objects.create(
                conta=instance,
                nome=cat_data["categoria"]
            )
            # Cria os itens dentro da categoria
            for item_data in cat_data["itens"]:
                ItemFAQ.objects.create(
                    conta=instance,
                    categoria=categoria,
                    intencao_chave=item_data["intencao_chave"],
                    perguntas_exemplo=item_data["perguntas_exemplo"],
                    resposta=item_data["resposta"]
                )
        print(f"--> FAQ padrão para '{instance.nome_conta}' populado com sucesso!")