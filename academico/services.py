from django.db import transaction
from django.utils import timezone

from .models import AnoLetivo, Aluno, ConfirmacaoMatricula
from escola.models import Turma


class AnoLetivoServiceError(Exception):
    pass


def get_ano_letivo_atual():
    """Retorna o ano letivo atual activo. Cria um padrão se ainda não existir."""
    ano_atual = AnoLetivo.objects.filter(atual=True).first()
    if ano_atual:
        return ano_atual.ano

    current_year = timezone.now().year
    ano_atual, created = AnoLetivo.objects.get_or_create(
        ano=current_year,
        defaults={'atual': True}
    )
    if not ano_atual.atual:
        ano_atual.atual = True
        ano_atual.save(update_fields=['atual'])
    return ano_atual.ano


def get_ano_letivo_obj_atual():
    """Retorna o objeto AnoLetivo actual, criando-o se necessário."""
    ano_atual = AnoLetivo.objects.filter(atual=True).first()
    if ano_atual:
        return ano_atual
    current_year = timezone.now().year
    return AnoLetivo.objects.create(ano=current_year, atual=True)


def ativar_ano_letivo(ano, migrar_alunos=True):
    """Define o ano letivo actual e move alunos activos para as turmas do novo ano."""
    with transaction.atomic():
        ano_antigo = AnoLetivo.objects.filter(atual=True).first()
        ano_novo = AnoLetivo.objects.activate(ano)

        if migrar_alunos and ano_antigo and ano_antigo.ano != ano_novo.ano:
            migrar_alunos_para_novo_ano(ano_antigo.ano, ano_novo.ano)

    return ano_novo


def migrar_alunos_para_novo_ano(ano_antigo, ano_novo):
    """Move alunos activos de um ano letivo anterior para turmas do ano novo."""
    alunos = Aluno.objects.filter(
        turma__ano_letivo=ano_antigo,
        esta_congelado=False,
    ).select_related('turma__curso', 'usuario')

    for aluno in alunos:
        turma_nova = None
        confirmacao = ConfirmacaoMatricula.objects.filter(
            aluno=aluno,
            ano_letivo=ano_novo,
            status='ATIVO'
        ).select_related('aluno__turma', 'curso_novo').order_by('-data_submissao').first()

        if confirmacao:
            turma_nova = buscar_turma_para_confirmacao(confirmacao, ano_novo)
        else:
            turma_nova = buscar_turma_para_aluno(aluno, ano_novo)

        if turma_nova and aluno.turma_id != turma_nova.id:
            aluno.turma = turma_nova
            aluno.save(update_fields=['turma'])


def buscar_turma_para_confirmacao(confirmacao, ano):
    curso = confirmacao.curso_novo or (confirmacao.aluno and confirmacao.aluno.turma.curso)
    filtro = {
        'classe': str(confirmacao.classe_nova),
        'ano_letivo': ano,
    }
    if curso:
        filtro['curso'] = curso

    turma = Turma.objects.filter(**filtro).first()
    if turma:
        return turma

    fallback = {
        'classe': str(confirmacao.classe_nova),
        'ano_letivo__gte': ano,
    }
    if curso:
        fallback['curso'] = curso

    return Turma.objects.filter(**fallback).order_by('ano_letivo').first()


def buscar_turma_para_aluno(aluno, ano):
    if not aluno.turma:
        return None

    proxima_classe = ConfirmacaoMatricula.calcular_proxima_classe(aluno.turma.classe) or aluno.turma.classe
    filtro = {
        'curso': aluno.turma.curso,
        'classe': proxima_classe,
        'ano_letivo': ano,
    }
    turma = Turma.objects.filter(**filtro).first()
    if turma:
        return turma

    return Turma.objects.filter(
        curso=aluno.turma.curso,
        classe=proxima_classe,
        ano_letivo__gte=ano,
    ).order_by('ano_letivo').first()
